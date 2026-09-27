"""
Product repository — all MongoDB queries for the products collection.

Key design decisions:
  - Server-side filtering: filters are applied as MongoDB query operators,
    not in Python after fetching all documents. This is critical for
    performance with a 44k-product catalog.
  - Pagination via .skip() + .limit() — computed in the repository,
    not in the service layer.
  - Text search uses MongoDB's built-in $text index (created in __init__.py).
"""

from pymongo.collection import Collection

from app.models.product import serialize_product
from app.utils.pagination import get_skip


class ProductRepository:
    def __init__(self, db):
        self.collection: Collection = db.products

    def find_all(
        self,
        page: int = 1,
        per_page: int = 20,
        category: str | None = None,
        brand: str | None = None,
        gender: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        size: str | None = None,
        color: str | None = None,
        sort_by: str | None = None,
        available_only: bool = True,
    ) -> tuple[list[dict], int]:
        """
        Fetch a filtered, sorted, paginated product list.

        Args:
            All filter parameters are optional; unset filters are ignored.
            available_only: When True, excludes out-of-stock products.

        Returns:
            (list of serialized product dicts, total count matching filters)
        """
        query = self._build_filter_query(
            category, brand, gender, min_price, max_price, size, color, available_only
        )

        total = self.collection.count_documents(query)
        sort = self._build_sort(sort_by)

        cursor = (
            self.collection.find(query)
            .sort(sort)
            .skip(get_skip(page, per_page))
            .limit(per_page)
        )

        return [serialize_product(doc) for doc in cursor], total

    def find_by_id(self, product_id: str) -> dict | None:
        """Fetch a single product by its stable product_id string."""
        doc = self.collection.find_one({"product_id": product_id})
        return serialize_product(doc)

    def find_by_ids(self, product_ids: list[str]) -> list[dict]:
        """
        Fetch multiple products by product_id list.
        Used by recommendation endpoints to hydrate product details.
        """
        cursor = self.collection.find({"product_id": {"$in": product_ids}})
        # Preserve the input ordering
        docs = {doc["product_id"]: serialize_product(doc) for doc in cursor}
        return [docs[pid] for pid in product_ids if pid in docs]

    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        category: str | None = None,
        gender: str | None = None,
    ) -> tuple[list[dict], int]:
        """
        Full-text search using MongoDB's $text index.

        The text index was created in app/__init__.py on 'name' and
        'description' fields. $text search is efficient for keyword lookup.
        It does NOT support fuzzy matching — for that, Elasticsearch would
        be a better choice (noted as a future improvement).
        """
        mongo_query: dict = {"$text": {"$search": query}}
        if category:
            mongo_query["category"] = category
        if gender:
            mongo_query["gender"] = gender
        mongo_query["is_available"] = True

        total = self.collection.count_documents(mongo_query)
        # Sort by text relevance score when searching
        cursor = (
            self.collection.find(
                mongo_query, {"score": {"$meta": "textScore"}}
            )
            .sort([("score", {"$meta": "textScore"})])
            .skip(get_skip(page, per_page))
            .limit(per_page)
        )

        return [serialize_product(doc) for doc in cursor], total

    def get_trending(self, category: str | None = None, top_k: int = 20) -> list[dict]:
        """
        Fetch trending products ranked by rating × log(review_count + 1).

        We use an aggregation pipeline to compute the trend score inside
        MongoDB so that we don't fetch all documents into Python memory.

        Note: This is a popularity heuristic, not a real CTR-based ranking.
        """
        match_stage: dict = {"$match": {"is_available": True}}
        if category:
            match_stage["$match"]["category"] = category

        pipeline = [
            match_stage,
            {
                "$addFields": {
                    "trend_score": {
                        "$multiply": [
                            "$rating",
                            {"$ln": {"$add": ["$review_count", 1]}},
                        ]
                    }
                }
            },
            {"$sort": {"trend_score": -1}},
            {"$limit": top_k},
        ]

        cursor = self.collection.aggregate(pipeline)
        return [serialize_product(doc) for doc in cursor]

    def get_categories(self) -> list[str]:
        """Return distinct category values (for filter UI)."""
        return sorted(self.collection.distinct("category", {"is_available": True}))

    def get_brands(self, category: str | None = None) -> list[str]:
        """Return distinct brand values, optionally filtered by category."""
        query = {"is_available": True}
        if category:
            query["category"] = category
        return sorted(self.collection.distinct("brand", query))

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _build_filter_query(
        self, category, brand, gender, min_price, max_price, size, color, available_only
    ) -> dict:
        """Build the MongoDB filter document from optional parameters."""
        query: dict = {}
        if available_only:
            query["is_available"] = True
        if category:
            query["category"] = category
        if brand:
            query["brand"] = brand
        if gender:
            query["gender"] = gender
        if size:
            query["sizes"] = size  # $in is implied: {"sizes": "M"} matches arrays containing "M"
        if color:
            query["colors"] = {"$regex": color, "$options": "i"}

        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = float(min_price)
        if max_price is not None:
            price_filter["$lte"] = float(max_price)
        if price_filter:
            query["discounted_price"] = price_filter

        return query

    def _build_sort(self, sort_by: str | None) -> list:
        """Map sort_by string to MongoDB sort specification."""
        sort_map = {
            "price_asc": [("discounted_price", 1)],
            "price_desc": [("discounted_price", -1)],
            "rating": [("rating", -1)],
            "popularity": [("review_count", -1)],
        }
        return sort_map.get(sort_by, [("created_at", -1)])
