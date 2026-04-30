from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from app.api.v1.auth import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get('/users')
async def list_users(user: dict = Depends(get_current_user), db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT u.id, u.username, u.avatar_url,
               CASE WHEN f.follower_id IS NULL THEN 0 ELSE 1 END as followed_by_me
        FROM users u
        LEFT JOIN user_follows f
          ON f.followee_id = u.id AND f.follower_id = ?
        WHERE u.id != ?
        ORDER BY u.username ASC
        """,
        (user['user_id'], user['user_id'])
    )
    return [dict(row) for row in cursor.fetchall()]


@router.post('/follow/{target_user_id}')
async def toggle_follow(
    target_user_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    if target_user_id == user['user_id']:
        raise HTTPException(status_code=400, detail='不能关注自己')

    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE id = ?', (target_user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail='用户不存在')

    cursor.execute(
        'SELECT 1 FROM user_follows WHERE follower_id = ? AND followee_id = ?',
        (user['user_id'], target_user_id)
    )
    exists = cursor.fetchone()
    if exists:
        cursor.execute(
            'DELETE FROM user_follows WHERE follower_id = ? AND followee_id = ?',
            (user['user_id'], target_user_id)
        )
        followed = False
    else:
        cursor.execute(
            'INSERT INTO user_follows (follower_id, followee_id) VALUES (?, ?)',
            (user['user_id'], target_user_id)
        )
        followed = True

    db.commit()
    return {'followed': followed}
