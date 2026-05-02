import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.services.recommendation_service import rank_articles_for_user, record_behavior

router = APIRouter()

class ArticleCreate(BaseModel):
    title: str
    content: str
    tag_ids: Optional[List[str]] = []

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tag_ids: Optional[List[str]] = None

class ArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    author: str
    created_at: str
    updated_at: str
    tags: List[dict] = []


class SquareArticleResponse(ArticleResponse):
    likes_count: int = 0
    comments_count: int = 0
    liked_by_me: bool = False
    recommend_score: float = 0.0
    recommend_reason: dict = {}


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: str
    article_id: str
    user_id: str
    username: str
    content: str
    created_at: str

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleCreate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    content_base64 = base64.b64encode(article.content.encode('utf-8')).decode('utf-8')
    article_id = str(uuid4())
    
    cursor.execute(
        "INSERT INTO articles (id, title, content, author) VALUES (?, ?, ?, ?)",
        (article_id, article.title, content_base64, user["sub"])
    )
    
    for tag_id in (article.tag_ids or []):
        cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
        if cursor.fetchone():
            cursor.execute(
                "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                (article_id, tag_id)
            )
    
    db.commit()
    return {"id": article_id, "message": "Article created successfully"}

@router.get("", response_model=List[ArticleResponse])
async def list_articles(db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT a.*, GROUP_CONCAT(t.id || ':' || t.name) as tag_list
        FROM articles a
        LEFT JOIN article_tags at ON a.id = at.article_id
        LEFT JOIN tags t ON at.tag_id = t.id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    """)
    articles = []
    for row in cursor.fetchall():
        tags = []
        if row["tag_list"]:
            for tag_str in row["tag_list"].split(","):
                if ":" in tag_str:
                    tid, tname = tag_str.split(":", 1)
                    tags.append({"id": tid, "name": tname})
        articles.append({
            "id": row["id"],
            "title": row["title"],
            "content": base64.b64decode(row["content"]).decode('utf-8'),
            "author": row["author"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "tags": tags
        })
    return articles


@router.get("/square", response_model=List[SquareArticleResponse])
async def list_square_articles(
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            a.*,
            tg.tag_list as tag_list,
            COALESCE(lk.likes_count, 0) as likes_count,
            COALESCE(cm.comments_count, 0) as comments_count,
            MAX(CASE WHEN al.user_id = ? THEN 1 ELSE 0 END) as liked_by_me,
            MAX(CASE WHEN uf.follower_id = ? AND uf.followee_id = u.id THEN 1 ELSE 0 END) as followed_author
        FROM articles a
        LEFT JOIN users u ON u.username = a.author
        LEFT JOIN (
            SELECT at.article_id, GROUP_CONCAT(t.id || ':' || t.name) as tag_list
            FROM article_tags at
            LEFT JOIN tags t ON at.tag_id = t.id
            GROUP BY at.article_id
        ) tg ON tg.article_id = a.id
        LEFT JOIN (
            SELECT article_id, COUNT(DISTINCT user_id) as likes_count
            FROM article_likes
            GROUP BY article_id
        ) lk ON lk.article_id = a.id
        LEFT JOIN (
            SELECT article_id, COUNT(DISTINCT id) as comments_count
            FROM article_comments
            GROUP BY article_id
        ) cm ON cm.article_id = a.id
        LEFT JOIN article_likes al ON a.id = al.article_id
        LEFT JOIN user_follows uf ON uf.followee_id = u.id
        GROUP BY a.id
        ORDER BY
          (MAX(CASE WHEN uf.follower_id = ? AND uf.followee_id = u.id THEN 1 ELSE 0 END) * 10
          + COALESCE(lk.likes_count, 0) * 2
          + COALESCE(cm.comments_count, 0) * 3
          + MAX(CASE WHEN al.user_id = ? THEN 1 ELSE 0 END) * 1) DESC,
          a.created_at DESC
    """, (user["user_id"], user["user_id"], user["user_id"], user["user_id"]))

    articles = []
    for row in cursor.fetchall():
        tags = []
        if row["tag_list"]:
            for tag_str in row["tag_list"].split(","):
                if ":" in tag_str:
                    tid, tname = tag_str.split(":", 1)
                    tags.append({"id": tid, "name": tname})
        articles.append({
            "id": row["id"],
            "title": row["title"],
            "content": base64.b64decode(row["content"]).decode('utf-8'),
            "author": row["author"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "tags": tags,
            "likes_count": row["likes_count"] or 0,
            "comments_count": row["comments_count"] or 0,
            "liked_by_me": bool(row["liked_by_me"]),
            "followed_author": bool(row["followed_author"])
        })

    ranked = rank_articles_for_user(db, user["user_id"], articles)
    for article in ranked:
        if "followed_author" in article:
            del article["followed_author"]
    return ranked


@router.post("/{article_id}/view")
async def mark_view(
    article_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Article not found")
    record_behavior(db, user["user_id"], article_id, "浏览")
    db.commit()
    return {"message": "ok"}


@router.post("/{article_id}/like")
async def toggle_like(
    article_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Article not found")

    cursor.execute(
        "SELECT 1 FROM article_likes WHERE article_id = ? AND user_id = ?",
        (article_id, user["user_id"])
    )
    exists = cursor.fetchone()
    if exists:
        cursor.execute(
            "DELETE FROM article_likes WHERE article_id = ? AND user_id = ?",
            (article_id, user["user_id"])
        )
        liked = False
    else:
        cursor.execute(
            "INSERT INTO article_likes (article_id, user_id) VALUES (?, ?)",
            (article_id, user["user_id"])
        )
        liked = True

    record_behavior(db, user["user_id"], article_id, "点赞")

    db.commit()
    cursor.execute("SELECT COUNT(*) as count FROM article_likes WHERE article_id = ?", (article_id,))
    count = cursor.fetchone()["count"]
    return {"liked": liked, "likes_count": count}


@router.get("/{article_id}/comments", response_model=List[CommentResponse])
async def list_comments(article_id: str, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, article_id, user_id, username, content, created_at
        FROM article_comments
        WHERE article_id = ?
        ORDER BY created_at DESC
        """,
        (article_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


@router.post("/{article_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    article_id: str,
    payload: CommentCreate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    cursor = db.cursor()
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Article not found")

    comment_id = str(uuid4())
    cursor.execute(
        """
        INSERT INTO article_comments (id, article_id, user_id, username, content)
        VALUES (?, ?, ?, ?, ?)
        """,
        (comment_id, article_id, user["user_id"], user["sub"], content)
    )
    record_behavior(db, user["user_id"], article_id, "评论")
    db.commit()
    cursor.execute(
        "SELECT id, article_id, user_id, username, content, created_at FROM article_comments WHERE id = ?",
        (comment_id,)
    )
    row = cursor.fetchone()
    return dict(row)


@router.delete("/{article_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    article_id: str,
    comment_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id, author FROM articles WHERE id = ?", (article_id,))
    article_row = cursor.fetchone()
    if not article_row:
        raise HTTPException(status_code=404, detail="Article not found")

    cursor.execute(
        "SELECT id, user_id FROM article_comments WHERE id = ? AND article_id = ?",
        (comment_id, article_id)
    )
    comment_row = cursor.fetchone()
    if not comment_row:
        raise HTTPException(status_code=404, detail="Comment not found")

    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user["user_id"],))
    current_user_row = cursor.fetchone()
    is_admin = bool(current_user_row and current_user_row["is_admin"])

    is_article_author = article_row["author"] == user["sub"]
    is_comment_owner = comment_row["user_id"] == user["user_id"]
    if not (is_admin or is_article_author or is_comment_owner):
        raise HTTPException(status_code=403, detail="No permission to delete this comment")

    cursor.execute("DELETE FROM article_comments WHERE id = ?", (comment_id,))
    db.commit()

@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")
    
    cursor.execute("""
        SELECT t.id, t.name FROM tags t
        JOIN article_tags at ON t.id = at.tag_id
        WHERE at.article_id = ?
    """, (article_id,))
    tags = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
    
    return {
        "id": row["id"],
        "title": row["title"],
        "content": base64.b64decode(row["content"]).decode('utf-8'),
        "author": row["author"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "tags": tags
    }

@router.put("/{article_id}")
async def update_article(
    article_id: str,
    article: ArticleUpdate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")
    
    updates = []
    params = []
    if article.title is not None:
        updates.append("title = ?")
        params.append(article.title)
    if article.content is not None:
        updates.append("content = ?")
        params.append(base64.b64encode(article.content.encode('utf-8')).decode('utf-8'))
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(article_id)
        cursor.execute(f"UPDATE articles SET {', '.join(updates)} WHERE id = ?", params)
    
    if article.tag_ids is not None:
        cursor.execute("DELETE FROM article_tags WHERE article_id = ?", (article_id,))
        for tag_id in (article.tag_ids or []):
            cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
            if cursor.fetchone():
                cursor.execute(
                    "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                    (article_id, tag_id)
                )
    
    db.commit()
    return {"message": "Article updated successfully"}

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    db.commit()
