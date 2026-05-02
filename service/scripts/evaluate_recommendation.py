import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.recommendation_service import rank_articles_for_user


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace(' ', 'T'))


def load_articles(conn: sqlite3.Connection):
    cursor = conn.cursor()
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
    result = []
    for row in cursor.fetchall():
        tags = []
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


def recall_at_k(ranked_ids, truth_ids, k):
    topk = ranked_ids[:k]
    hit = len(set(topk) & set(truth_ids))
    return hit / max(1, len(set(truth_ids)))


def ndcg_at_k(ranked_ids, truth_ids, k):
    gains = []
    truth_set = set(truth_ids)
    for idx, aid in enumerate(ranked_ids[:k], start=1):
        rel = 1 if aid in truth_set else 0
        gains.append(rel / (idx.bit_length() if idx > 1 else 1))
    dcg = sum(gains)
    ideal_len = min(k, len(truth_set))
    idcg = sum((1 / (idx.bit_length() if idx > 1 else 1)) for idx in range(1, ideal_len + 1))
    return dcg / idcg if idcg > 0 else 0.0


def run(mode: int, k: int, output: Path):
    db_path = Path(__file__).resolve().parents[1] / 'social_algorithm.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT key, value FROM algorithm_settings')
    settings = {row['key']: float(row['value']) for row in cursor.fetchall()}
    settings['algo_mode'] = float(mode)
    for key, value in settings.items():
        cursor.execute(
            'INSERT OR REPLACE INTO algorithm_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (key, value)
        )
    conn.commit()

    articles = load_articles(conn)

    cursor.execute(
        """
        SELECT user_id, article_id, MAX(created_at) AS last_time
        FROM user_behaviors
        GROUP BY user_id, article_id
        """
    )
    by_user = defaultdict(list)
    for row in cursor.fetchall():
        by_user[row['user_id']].append((row['article_id'], parse_dt(str(row['last_time']))))

    rows = []
    recalls = []
    ndcgs = []
    for user_id, items in by_user.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda t: t[1])
        truth_id = items[-1][0]

        ranked = rank_articles_for_user(conn, user_id, [dict(a) for a in articles])
        ranked_ids = [a['id'] for a in ranked]

        r = recall_at_k(ranked_ids, [truth_id], k)
        n = ndcg_at_k(ranked_ids, [truth_id], k)
        recalls.append(r)
        ndcgs.append(n)
        rows.append({'user_id': user_id, 'truth_article': truth_id, f'recall@{k}': r, f'ndcg@{k}': n})

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['user_id', 'truth_article', f'recall@{k}', f'ndcg@{k}'])
        writer.writeheader()
        writer.writerows(rows)

    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    avg_ndcg = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0
    print(f'mode={mode}, users={len(rows)}, recall@{k}={avg_recall:.4f}, ndcg@{k}={avg_ndcg:.4f}')
    print(f'report={output}')

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate recommendation model offline')
    parser.add_argument('--mode', type=int, default=0, choices=[0, 1, 2, 3], help='0 full, 1 hot_only, 2 similarity_only, 3 sim_hot')
    parser.add_argument('--k', type=int, default=10)
    parser.add_argument('--output', type=str, default='reports/eval_mode_0.csv')
    args = parser.parse_args()
    run(args.mode, args.k, Path(args.output))
