from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
from pydantic import BaseModel
from typing import List
from uuid import uuid4
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_user

router = APIRouter()

class TagCreate(BaseModel):
    name: str

class TagUpdate(BaseModel):
    name: str

class TagResponse(BaseModel):
    id: str
    name: str
    created_at: str
    article_count: int = 0
    related_user_count: int = 0


class PushCandidate(BaseModel):
    user_id: str
    username: str
    avatar_url: str | None = None
    score: float
    push_discipline: str
    reason: str


class PushPreviewResponse(BaseModel):
    tag_name: str
    candidates: List[PushCandidate]


def _recommend_users_for_tag(db: Connection, current_user_id: str, tag_name: str, limit: int = 8) -> List[dict]:
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, username, avatar_url
        FROM users
        WHERE id != ?
        ORDER BY username ASC
        """,
        (current_user_id,)
    )
    users = cursor.fetchall()

    now = datetime.now()
    ranked: List[dict] = []

    for user_row in users:
        target_user_id = user_row["id"]

        cursor.execute(
            """
            SELECT category, weight, created_at
            FROM user_behaviors
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 300
            """,
            (target_user_id,)
        )
        behavior_rows = cursor.fetchall()

        tag_interest_score = 0.0
        recent_active_count = 0
        total_weight = 0.0

        for behavior in behavior_rows:
            created_at_str = str(behavior["created_at"])
            created_at_text = created_at_str.replace(" ", "T")
            try:
                created_at = datetime.fromisoformat(created_at_text)
            except ValueError:
                created_at = now

            days = max(0, (now - created_at).days)
            decay = 0.95 ** days
            weighted_value = float(behavior["weight"]) * decay
            total_weight += weighted_value

            if behavior["category"] == tag_name:
                tag_interest_score += weighted_value
            if days <= 30:
                recent_active_count += 1

        behavior_score = 0.0
        if total_weight > 0:
            behavior_score = min(1.0, tag_interest_score / total_weight)

        cursor.execute(
            "SELECT 1 FROM user_follows WHERE follower_id = ? AND followee_id = ?",
            (current_user_id, target_user_id)
        )
        i_follow_target = 1.0 if cursor.fetchone() else 0.0

        cursor.execute(
            "SELECT 1 FROM user_follows WHERE follower_id = ? AND followee_id = ?",
            (target_user_id, current_user_id)
        )
        target_follows_me = 1.0 if cursor.fetchone() else 0.0

        social_score = min(1.0, i_follow_target * 0.7 + target_follows_me * 0.3)
        active_score = min(1.0, recent_active_count / 12.0)

        final_score = behavior_score * 0.7 + social_score * 0.2 + active_score * 0.1

        if final_score >= 0.75:
            push_discipline = "高优先级：每日 1 次"
        elif final_score >= 0.45:
            push_discipline = "中优先级：每周 3 次"
        else:
            push_discipline = "低优先级：每周 1 次"

        reason_parts = []
        if behavior_score > 0:
            reason_parts.append("该用户在此标签下有历史行为")
        if i_follow_target > 0:
            reason_parts.append("你已关注该用户")
        if target_follows_me > 0:
            reason_parts.append("该用户关注了你")
        if active_score >= 0.3:
            reason_parts.append("近 30 天活跃")
        if not reason_parts:
            reason_parts.append("基于全局活跃度补充推荐")

        ranked.append(
            {
                "user_id": target_user_id,
                "username": user_row["username"],
                "avatar_url": user_row["avatar_url"],
                "score": round(final_score, 4),
                "push_discipline": push_discipline,
                "reason": "；".join(reason_parts),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]


@router.get("/preview/push-users", response_model=PushPreviewResponse)
async def preview_push_users(
    name: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    tag_name = name.strip()
    if not tag_name:
        raise HTTPException(status_code=400, detail="标签名称不能为空")

    candidates = _recommend_users_for_tag(db, user["user_id"], tag_name)
    return {"tag_name": tag_name, "candidates": candidates}

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagCreate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    try:
        tag_id = str(uuid4())
        cursor.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (tag_id, tag.name))
        db.commit()
        return {"id": tag_id, "message": "Tag created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Tag name already exists")

@router.get("", response_model=List[TagResponse])
async def list_tags(db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT
            t.id,
            t.name,
            t.created_at,
            COUNT(DISTINCT at.article_id) AS article_count,
            (
              SELECT COUNT(DISTINCT uid) FROM (
                SELECT ub2.user_id AS uid
                FROM user_behaviors ub2
                WHERE ub2.category = t.name
                UNION
                SELECT u2.id AS uid
                FROM article_tags at2
                JOIN articles a2 ON a2.id = at2.article_id
                JOIN users u2 ON u2.username = a2.author
                WHERE at2.tag_id = t.id
              )
            ) AS related_user_count
        FROM tags t
        LEFT JOIN article_tags at ON at.tag_id = t.id
        GROUP BY t.id, t.name, t.created_at
        ORDER BY t.name
        """
    )
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "created_at": row["created_at"],
            "article_count": int(row["article_count"] or 0),
            "related_user_count": int(row["related_user_count"] or 0)
        }
        for row in cursor.fetchall()
    ]

@router.put("/{tag_id}")
async def update_tag(
    tag_id: str,
    tag: TagUpdate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tag not found")
    
    try:
        cursor.execute("UPDATE tags SET name = ? WHERE id = ?", (tag.name, tag_id))
        db.commit()
        return {"message": "Tag updated successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Tag name already exists")

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # 删除标签时，清除关联文章的所有标签（根据需求：将关联标签的文章的标签都清除）
    # 如果只需要清除被删除标签的关联，删除下面这行
    cursor.execute("DELETE FROM article_tags WHERE tag_id = ?", (tag_id,))
    # 如果需要清除关联文章的所有标签，使用下面这行代替上行
    # cursor.execute("DELETE FROM article_tags WHERE article_id IN (SELECT article_id FROM article_tags WHERE tag_id = ?)", (tag_id,))
    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    db.commit()
