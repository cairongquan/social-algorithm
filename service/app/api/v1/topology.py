from fastapi import APIRouter, Depends
from sqlite3 import Connection

from app.api.v1.auth import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get('/overview')
async def topology_overview(user: dict = Depends(get_current_user), db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) as c FROM users')
    users_count = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM user_follows')
    follows_count = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM article_likes')
    likes_count = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM article_comments')
    comments_count = cursor.fetchone()['c']

    cursor.execute('SELECT COUNT(*) as c FROM user_follows WHERE follower_id = ?', (user['user_id'],))
    my_following = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM user_follows WHERE followee_id = ?', (user['user_id'],))
    my_followers = cursor.fetchone()['c']

    score = my_followers * 2 + my_following + likes_count * 0.1 + comments_count * 0.2
    return {
        'users_count': users_count,
        'follows_count': follows_count,
        'likes_count': likes_count,
        'comments_count': comments_count,
        'my_following': my_following,
        'my_followers': my_followers,
        'my_attention_score': round(score, 2)
    }


@router.get('/graph')
async def topology_graph(user: dict = Depends(get_current_user), db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('SELECT id, username, avatar_url FROM users ORDER BY username ASC')
    nodes = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT follower_id, followee_id FROM user_follows')
    edges = [dict(row) for row in cursor.fetchall()]

    return {'nodes': nodes, 'edges': edges}
