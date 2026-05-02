from fastapi import APIRouter, Depends
from sqlite3 import Connection

from app.api.v1.auth import require_admin
from app.core.database import get_db

router = APIRouter()


@router.get('/overview')
async def topology_overview(user: dict = Depends(require_admin), db: Connection = Depends(get_db)):
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
async def topology_graph(user: dict = Depends(require_admin), db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('SELECT id, username, avatar_url FROM users ORDER BY username ASC')
    user_nodes = [
        {
            'id': f"user:{row['id']}",
            'name': row['username'],
            'node_type': 'user',
            'avatar_url': row['avatar_url']
        }
        for row in cursor.fetchall()
    ]

    cursor.execute('SELECT id, name FROM tags ORDER BY name ASC')
    tag_nodes = [
        {
            'id': f"tag:{row['id']}",
            'name': row['name'],
            'node_type': 'tag'
        }
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT
            ub.user_id,
            t.id as tag_id,
            t.name as tag_name,
            COUNT(*) as behavior_count,
            SUM(ub.weight) as behavior_weight
        FROM user_behaviors ub
        JOIN tags t ON t.name = ub.category
        GROUP BY ub.user_id, t.id, t.name
        """
    )
    behavior_edges = {}
    for row in cursor.fetchall():
        key = (row['user_id'], row['tag_id'])
        behavior_edges[key] = {
            'source': f"user:{row['user_id']}",
            'target': f"tag:{row['tag_id']}",
            'relation': 'behavior',
            'weight': round(float(row['behavior_weight'] or 0), 4),
            'count': int(row['behavior_count'] or 0),
            'tag_name': row['tag_name']
        }

    cursor.execute(
        """
        SELECT
            u.id as user_id,
            t.id as tag_id,
            t.name as tag_name,
            COUNT(DISTINCT a.id) as article_count
        FROM users u
        JOIN articles a ON a.author = u.username
        JOIN article_tags at ON at.article_id = a.id
        JOIN tags t ON t.id = at.tag_id
        GROUP BY u.id, t.id, t.name
        """
    )

    for row in cursor.fetchall():
        key = (row['user_id'], row['tag_id'])
        article_count = int(row['article_count'] or 0)
        if key in behavior_edges:
            behavior_edges[key]['relation'] = 'behavior+author'
            behavior_edges[key]['count'] += article_count
            behavior_edges[key]['weight'] = round(behavior_edges[key]['weight'] + article_count * 0.5, 4)
        else:
            behavior_edges[key] = {
                'source': f"user:{row['user_id']}",
                'target': f"tag:{row['tag_id']}",
                'relation': 'author',
                'weight': round(article_count * 0.5, 4),
                'count': article_count,
                'tag_name': row['tag_name']
            }

    return {
        'nodes': user_nodes + tag_nodes,
        'edges': list(behavior_edges.values())
    }
