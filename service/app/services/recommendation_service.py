import math
from collections import defaultdict
from datetime import datetime
from sqlite3 import Connection


class SimilarityCalculator:
    @staticmethod
    def cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
        if not vec1 or not vec2:
            return 0.0

        common_keys = set(vec1.keys()) & set(vec2.keys())
        if not common_keys:
            return 0.0

        dot_product = sum(vec1[key] * vec2[key] for key in common_keys)
        magnitude1 = math.sqrt(sum(value * value for value in vec1.values()))
        magnitude2 = math.sqrt(sum(value * value for value in vec2.values()))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)


class UserInterestModel:
    def __init__(self, decay_factor: float = 0.95):
        self.decay_factor = decay_factor
        self.user_interest_vectors = defaultdict(lambda: defaultdict(float))

    def add_behavior(self, user_id: str, category: str, weight: float, timestamp: datetime):
        self._update_interest_vector(user_id, category, weight, timestamp)

    def _update_interest_vector(self, user_id: str, category: str, weight: float, timestamp: datetime):
        time_diff = datetime.now() - timestamp
        days_passed = max(0, time_diff.days)
        decay = math.pow(self.decay_factor, days_passed)
        effective_weight = weight * decay
        self.user_interest_vectors[user_id][category] += effective_weight

    def normalize_interest_vector(self, user_id: str) -> dict[str, float]:
        vector = dict(self.user_interest_vectors[user_id])
        if not vector:
            return {}
        total = sum(vector.values())
        if total <= 0:
            return vector
        return {key: value / total for key, value in vector.items()}


BEHAVIOR_WEIGHTS = {
    '浏览': 0.3,
    '点击': 0.7,
    '点赞': 0.8,
    '评论': 0.9,
}


def record_behavior(db: Connection, user_id: str, article_id: str, behavior_type: str):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT t.name
        FROM tags t
        JOIN article_tags at ON t.id = at.tag_id
        WHERE at.article_id = ?
        """,
        (article_id,)
    )
    tags = [row['name'] for row in cursor.fetchall()]
    if not tags:
        tags = ['未分类']

    weight = BEHAVIOR_WEIGHTS.get(behavior_type, 0.5)
    for category in tags:
        cursor.execute(
            """
            INSERT INTO user_behaviors (id, user_id, article_id, category, behavior_type, weight)
            VALUES (lower(hex(randomblob(16))), ?, ?, ?, ?, ?)
            """,
            (user_id, article_id, category, behavior_type, weight)
        )


def rank_articles_for_user(db: Connection, user_id: str, articles: list[dict]) -> list[dict]:
    cursor = db.cursor()

    cursor.execute('SELECT key, value FROM algorithm_settings')
    raw_settings = {row['key']: float(row['value']) for row in cursor.fetchall()}
    decay_factor = raw_settings.get('decay_factor', 0.95)
    similarity_weight = raw_settings.get('similarity_weight', 0.6)
    hot_weight = raw_settings.get('hot_weight', 0.2)
    follow_weight = raw_settings.get('follow_weight', 0.15)
    liked_weight = raw_settings.get('liked_weight', 0.05)
    diversity_penalty_default = raw_settings.get('diversity_penalty', 0.2)
    hot_like_factor = raw_settings.get('hot_like_factor', 0.15)
    hot_comment_factor = raw_settings.get('hot_comment_factor', 0.25)
    algo_mode = int(raw_settings.get('algo_mode', 0))

    # 构建用户兴趣向量
    model = UserInterestModel(decay_factor=decay_factor)
    cursor.execute(
        """
        SELECT category, weight, created_at
        FROM user_behaviors
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 500
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    for row in rows:
        timestamp = datetime.fromisoformat(str(row['created_at']).replace(' ', 'T'))
        model.add_behavior(user_id, row['category'], float(row['weight']), timestamp)
    user_vector = model.normalize_interest_vector(user_id)

    scored = []
    seen_categories: set[str] = set()
    for article in articles:
        content_vector = {tag['name']: 1.0 for tag in article['tags']} if article['tags'] else {'未分类': 1.0}
        similarity = SimilarityCalculator.cosine_similarity(user_vector, content_vector)

        hot_score = article['likes_count'] * hot_like_factor + article['comments_count'] * hot_comment_factor
        follow_bonus = 1.0 if article.get('followed_author') else 0.0
        liked_bonus = 0.2 if article.get('liked_by_me') else 0.0

        diversity_penalty = 0.0
        common = set(content_vector.keys()) & seen_categories
        if common:
            diversity_penalty = diversity_penalty_default

        similarity_part = similarity * similarity_weight
        hot_part = hot_score * hot_weight
        follow_part = follow_bonus * follow_weight
        liked_part = liked_bonus * liked_weight
        penalty_part = diversity_penalty

        if algo_mode == 1:
            final_score = hot_part
            mode_name = 'hot_only'
        elif algo_mode == 2:
            final_score = similarity_part
            mode_name = 'similarity_only'
        elif algo_mode == 3:
            final_score = similarity_part + hot_part
            mode_name = 'sim_hot'
        else:
            final_score = similarity_part + hot_part + follow_part + liked_part - penalty_part
            mode_name = 'full_model'

        article['recommend_score'] = round(final_score, 6)
        article['recommend_reason'] = {
            'tip': '我为什么会刷到这篇文章',
            'mode': mode_name,
            'matched_tags': list(content_vector.keys()),
            'similarity_score': round(similarity, 6),
            'hot_score': round(hot_score, 6),
            'follow_bonus': round(follow_bonus, 6),
            'liked_bonus': round(liked_bonus, 6),
            'diversity_penalty': round(diversity_penalty, 6),
            'formula': {
                'similarity_part': round(similarity_part, 6),
                'hot_part': round(hot_part, 6),
                'follow_part': round(follow_part, 6),
                'liked_part': round(liked_part, 6),
                'penalty_part': round(penalty_part, 6),
            }
        }
        scored.append(article)

        for name in content_vector.keys():
            seen_categories.add(name)

    scored.sort(key=lambda item: (item['recommend_score'], item['created_at']), reverse=True)
    return scored
