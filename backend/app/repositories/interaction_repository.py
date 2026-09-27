"""
Interaction repository — all MongoDB queries for the interactions collection.
"""

from pymongo.collection import Collection
from bson import ObjectId

from app.models.interaction import build_interaction, serialize_interaction
from app.utils.pagination import get_skip


class InteractionRepository:
    def __init__(self, db):
        self.collection: Collection = db.interactions

    def log(
        self,
        user_id,
        product_id: str,
        interaction_type: str,
        weights: dict,
        session_id: str | None = None,
    ) -> dict:
        """Insert a new interaction document and return it."""
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except Exception:
                pass
        doc = build_interaction(user_id, product_id, interaction_type, weights, session_id)
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_interaction(doc)

    def find_by_user(
        self,
        user_id,
        interaction_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Fetch paginated interaction history for a user.
        Optionally filter by interaction_type.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        query = {"user_id": user_id}
        if interaction_type:
            query["interaction_type"] = interaction_type

        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("timestamp", -1)  # Most recent first
            .skip(get_skip(page, per_page))
            .limit(per_page)
        )
        return [serialize_interaction(doc) for doc in cursor], total

    def get_user_product_weights(self, user_id) -> dict[str, float]:
        """
        Aggregate all interactions for a user into a product_id → total_weight dict.

        This is the core input for personalized recommendations.
        We use an aggregation pipeline to do the summation in MongoDB,
        not in Python — avoids fetching every interaction document.

        Example output:
            {"P000042": 3.5, "P000017": 2.0, "P000099": 0.5}

        Time complexity: O(n) where n = number of interactions for this user.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$product_id",
                    "total_weight": {"$sum": "$weight"},
                }
            },
            {"$sort": {"total_weight": -1}},
        ]

        result = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["total_weight"] for doc in result}

    def get_popular_products(self, top_k: int = 50) -> list[str]:
        """
        Return the most interacted-with product IDs across all users.
        Used as a fallback for new users (cold-start).
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$product_id",
                    "total_weight": {"$sum": "$weight"},
                }
            },
            {"$sort": {"total_weight": -1}},
            {"$limit": top_k},
        ]
        result = self.collection.aggregate(pipeline)
        return [doc["_id"] for doc in result]

    def get_all_interactions_matrix(self) -> dict[str, dict[str, float]]:
        """
        Build a user_id → {product_id → weight} matrix for collaborative filtering.

        WARNING: This loads all interactions into memory. Only feasible for
        development/small datasets. For production, use batch processing or
        a dedicated ML pipeline.

        Returns:
            Dict mapping user_id_str → {product_id → total_weight}
        """
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "product_id": "$product_id",
                    },
                    "total_weight": {"$sum": "$weight"},
                }
            }
        ]

        matrix: dict[str, dict[str, float]] = {}
        for doc in self.collection.aggregate(pipeline):
            uid = str(doc["_id"]["user_id"])
            pid = doc["_id"]["product_id"]
            if uid not in matrix:
                matrix[uid] = {}
            matrix[uid][pid] = doc["total_weight"]

        return matrix
