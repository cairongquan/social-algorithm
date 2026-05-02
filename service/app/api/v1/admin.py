from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlite3 import Connection
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import csv

from PIL import Image, ImageDraw

from app.api.v1.auth import require_admin, get_current_user
from app.core.database import get_db
from app.services.recommendation_service import rank_articles_for_user

router = APIRouter()

DEFAULT_SETTINGS = {
    "decay_factor": 0.95,
    "similarity_weight": 0.6,
    "hot_weight": 0.2,
    "follow_weight": 0.15,
    "liked_weight": 0.05,
    "diversity_penalty": 0.2,
    "hot_like_factor": 0.15,
    "hot_comment_factor": 0.25,
    "algo_mode": 0,
}

SETTING_RANGES = {
    "decay_factor": (0.5, 0.9999),
    "similarity_weight": (0.0, 1.0),
    "hot_weight": (0.0, 1.0),
    "follow_weight": (0.0, 1.0),
    "liked_weight": (0.0, 1.0),
    "diversity_penalty": (0.0, 1.0),
    "hot_like_factor": (0.0, 2.0),
    "hot_comment_factor": (0.0, 2.0),
    "algo_mode": (0.0, 3.0),
}


class AlgorithmSettingsResponse(BaseModel):
    decay_factor: float
    similarity_weight: float
    hot_weight: float
    follow_weight: float
    liked_weight: float
    diversity_penalty: float
    hot_like_factor: float
    hot_comment_factor: float
    algo_mode: float


class AlgorithmCurrentResponse(AlgorithmSettingsResponse):
    mode_name: str


class AlgorithmSettingsUpdate(BaseModel):
    decay_factor: float
    similarity_weight: float
    hot_weight: float
    follow_weight: float
    liked_weight: float
    diversity_penalty: float
    hot_like_factor: float
    hot_comment_factor: float
    algo_mode: float


class ExperimentSummary(BaseModel):
    mode: int
    mode_name: str
    users: int
    recall_at_10: float
    ndcg_at_10: float


class ExperimentReportResponse(BaseModel):
    generated_at: str
    summaries: list[ExperimentSummary]
    csv_url: str
    md_url: str
    png_url: str


def _load_settings(db: Connection) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT key, value FROM algorithm_settings")
    result = {row["key"]: float(row["value"]) for row in cursor.fetchall()}
    return {
        key: result.get(key, value) for key, value in DEFAULT_SETTINGS.items()
    }


def _validate_settings(data: dict):
    weight_sum = data["similarity_weight"] + data["hot_weight"] + data["follow_weight"] + data["liked_weight"]
    if abs(weight_sum - 1.0) > 1e-6:
        raise HTTPException(status_code=400, detail="四项权重之和必须等于 1")

    for key, value in data.items():
        low, high = SETTING_RANGES[key]
        if value < low or value > high:
            raise HTTPException(status_code=400, detail=f"{key} 超出范围 [{low}, {high}]")

    if int(data["algo_mode"]) not in [0, 1, 2, 3]:
        raise HTTPException(status_code=400, detail="algo_mode 仅支持 0/1/2/3")


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace(' ', 'T'))


def _recall_at_k(ranked_ids: list[str], truth_ids: list[str], k: int) -> float:
    topk = ranked_ids[:k]
    hit = len(set(topk) & set(truth_ids))
    return hit / max(1, len(set(truth_ids)))


def _ndcg_at_k(ranked_ids: list[str], truth_ids: list[str], k: int) -> float:
    truth_set = set(truth_ids)
    dcg = 0.0
    for idx, aid in enumerate(ranked_ids[:k], start=1):
        rel = 1.0 if aid in truth_set else 0.0
        denom = 1.0 if idx == 1 else (idx.bit_length())
        dcg += rel / denom
    ideal_len = min(k, len(truth_set))
    idcg = 0.0
    for idx in range(1, ideal_len + 1):
        denom = 1.0 if idx == 1 else (idx.bit_length())
        idcg += 1.0 / denom
    return dcg / idcg if idcg > 0 else 0.0


def _load_articles_for_eval(db: Connection) -> list[dict]:
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT a.id, a.title, a.author, a.created_at, a.updated_at,
               tg.tag_list,
               COALESCE(lk.likes_count, 0) AS likes_count,
               COALESCE(cm.comments_count, 0) AS comments_count
        FROM articles a
        LEFT JOIN (
            SELECT at.article_id, GROUP_CONCAT(t.id || ':' || t.name) AS tag_list
            FROM article_tags at
            LEFT JOIN tags t ON at.tag_id = t.id
            GROUP BY at.article_id
        ) tg ON tg.article_id = a.id
        LEFT JOIN (
            SELECT article_id, COUNT(DISTINCT user_id) AS likes_count
            FROM article_likes
            GROUP BY article_id
        ) lk ON lk.article_id = a.id
        LEFT JOIN (
            SELECT article_id, COUNT(DISTINCT id) AS comments_count
            FROM article_comments
            GROUP BY article_id
        ) cm ON cm.article_id = a.id
        """
    )
    result: list[dict] = []
    for row in cursor.fetchall():
        tags: list[dict] = []
        if row[5]:
            for item in str(row[5]).split(','):
                if ':' in item:
                    tid, name = item.split(':', 1)
                    tags.append({'id': tid, 'name': name})
        result.append({
            'id': row[0],
            'title': row[1],
            'author': row[2],
            'created_at': row[3],
            'updated_at': row[4],
            'tags': tags,
            'likes_count': row[6],
            'comments_count': row[7],
            'liked_by_me': False,
            'followed_author': False,
        })
    return result


def _evaluate_mode(db: Connection, mode: int, k: int = 10) -> dict:
    cursor = db.cursor()
    cursor.execute('SELECT key, value FROM algorithm_settings')
    settings = {row['key']: float(row['value']) for row in cursor.fetchall()}
    settings['algo_mode'] = float(mode)
    for key, value in settings.items():
        cursor.execute(
            'INSERT OR REPLACE INTO algorithm_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (key, value)
        )
    db.commit()

    articles = _load_articles_for_eval(db)
    cursor.execute(
        """
        SELECT user_id, article_id, MAX(created_at) AS last_time
        FROM user_behaviors
        GROUP BY user_id, article_id
        """
    )
    by_user = defaultdict(list)
    for row in cursor.fetchall():
        by_user[row['user_id']].append((row['article_id'], _parse_dt(str(row['last_time']))))

    recalls: list[float] = []
    ndcgs: list[float] = []
    users = 0
    for user_id, items in by_user.items():
        if len(items) < 2:
            continue
        users += 1
        items.sort(key=lambda t: t[1])
        truth_id = items[-1][0]
        ranked = rank_articles_for_user(db, user_id, [dict(a) for a in articles])
        ranked_ids = [a['id'] for a in ranked]
        recalls.append(_recall_at_k(ranked_ids, [truth_id], k))
        ndcgs.append(_ndcg_at_k(ranked_ids, [truth_id], k))

    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    avg_ndcg = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0
    mode_map = {
        0: 'full_model',
        1: 'hot_only',
        2: 'similarity_only',
        3: 'sim_hot'
    }
    return {
        'mode': mode,
        'mode_name': mode_map.get(mode, 'full_model'),
        'users': users,
        'recall_at_10': round(avg_recall, 4),
        'ndcg_at_10': round(avg_ndcg, 4),
    }


def _write_chart_png(path: Path, summaries: list[dict]):
    width, height = 920, 460
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, width - 40, height - 40), outline='black', width=2)
    draw.text((52, 52), 'Offline Experiment Summary (Recall@10 / NDCG@10)', fill='black')

    bar_base_y = 380
    chart_top = 120
    chart_height = bar_base_y - chart_top
    groups = len(summaries)
    group_width = 180
    start_x = 80

    for idx, row in enumerate(summaries):
        gx = start_x + idx * group_width
        recall_h = int(chart_height * row['recall_at_10'])
        ndcg_h = int(chart_height * row['ndcg_at_10'])
        draw.rectangle((gx, bar_base_y - recall_h, gx + 46, bar_base_y), outline='black', fill='black')
        draw.rectangle((gx + 60, bar_base_y - ndcg_h, gx + 106, bar_base_y), outline='black', fill='white')
        draw.text((gx, bar_base_y + 10), f"mode {row['mode']}", fill='black')
        draw.text((gx, bar_base_y - recall_h - 16), f"R:{row['recall_at_10']}", fill='black')
        draw.text((gx + 60, bar_base_y - ndcg_h - 16), f"N:{row['ndcg_at_10']}", fill='black')

    draw.text((52, 410), 'Legend: Black=Recall@10, White=NDCG@10', fill='black')
    image.save(str(path), format='PNG')


@router.get('/algorithm-settings', response_model=AlgorithmSettingsResponse)
async def get_algorithm_settings(
    _: dict = Depends(require_admin),
    db: Connection = Depends(get_db)
):
    return _load_settings(db)


@router.get('/algorithm-settings/current', response_model=AlgorithmCurrentResponse)
async def get_algorithm_settings_current(
    _: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    data = _load_settings(db)
    mode = int(data.get('algo_mode', 0))
    mode_map = {
        0: 'full_model',
        1: 'hot_only',
        2: 'similarity_only',
        3: 'sim_hot'
    }
    data['mode_name'] = mode_map.get(mode, 'full_model')
    return data


@router.put('/algorithm-settings', response_model=AlgorithmSettingsResponse)
async def update_algorithm_settings(
    payload: AlgorithmSettingsUpdate,
    _: dict = Depends(require_admin),
    db: Connection = Depends(get_db)
):
    data = payload.model_dump()
    _validate_settings(data)
    cursor = db.cursor()
    for key, value in data.items():
        cursor.execute(
            "INSERT OR REPLACE INTO algorithm_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, float(value))
        )
    db.commit()
    return _load_settings(db)


@router.post('/algorithm-settings/reset', response_model=AlgorithmSettingsResponse)
async def reset_algorithm_settings(
    _: dict = Depends(require_admin),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    for key, value in DEFAULT_SETTINGS.items():
        cursor.execute(
            "INSERT OR REPLACE INTO algorithm_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, value)
        )
    db.commit()
    return _load_settings(db)


@router.post('/experiment-report', response_model=ExperimentReportResponse)
async def generate_experiment_report(
    _: dict = Depends(require_admin),
    db: Connection = Depends(get_db)
):
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = Path(__file__).resolve().parents[3] / 'reports'
    report_dir.mkdir(parents=True, exist_ok=True)

    summaries = [_evaluate_mode(db, mode, 10) for mode in [0, 1, 2, 3]]

    csv_name = f'experiment_summary_{now}.csv'
    md_name = f'experiment_summary_{now}.md'
    png_name = f'experiment_summary_{now}.png'

    csv_path = report_dir / csv_name
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['mode', 'mode_name', 'users', 'recall_at_10', 'ndcg_at_10'])
        writer.writeheader()
        writer.writerows(summaries)

    md_path = report_dir / md_name
    lines = [
        '# 推荐算法实验汇总',
        '',
        f'- 生成时间: {now}',
        '',
        '| mode | mode_name | users | recall@10 | ndcg@10 |',
        '|---|---|---:|---:|---:|',
    ]
    for row in summaries:
        lines.append(f"| {row['mode']} | {row['mode_name']} | {row['users']} | {row['recall_at_10']} | {row['ndcg_at_10']} |")
    lines.append('')
    lines.append('- mode 0: full_model')
    lines.append('- mode 1: hot_only')
    lines.append('- mode 2: similarity_only')
    lines.append('- mode 3: sim_hot')
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    png_path = report_dir / png_name
    _write_chart_png(png_path, summaries)

    return {
        'generated_at': now,
        'summaries': summaries,
        'csv_url': f'/api/v1/admin/experiment-report/files/{csv_name}',
        'md_url': f'/api/v1/admin/experiment-report/files/{md_name}',
        'png_url': f'/api/v1/admin/experiment-report/files/{png_name}',
    }


@router.get('/experiment-report/files/{filename}')
async def download_experiment_report_file(
    filename: str,
    _: dict = Depends(require_admin)
):
    safe_name = Path(filename).name
    report_dir = Path(__file__).resolve().parents[3] / 'reports'
    file_path = report_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='文件不存在')
    return FileResponse(path=str(file_path), filename=safe_name)
