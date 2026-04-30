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

    # 构建用户兴趣向量
    model = UserInterestModel(decay_factor=0.95)
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

        hot_score = article['likes_count'] * 0.15 + article['comments_count'] * 0.25
        follow_bonus = 1.0 if article.get('followed_author') else 0.0
        liked_bonus = 0.2 if article.get('liked_by_me') else 0.0

        diversity_penalty = 0.0
        common = set(content_vector.keys()) & seen_categories
        if common:
            diversity_penalty = 0.2

        final_score = similarity * 0.6 + hot_score * 0.2 + follow_bonus * 0.15 + liked_bonus * 0.05 - diversity_penalty
        article['recommend_score'] = round(final_score, 6)
        scored.append(article)

        for name in content_vector.keys():
            seen_categories.add(name)

    scored.sort(key=lambda item: (item['recommend_score'], item['created_at']), reverse=True)
    return scored
