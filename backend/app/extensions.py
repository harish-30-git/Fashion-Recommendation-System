"""
Flask extension instances for StyleSense.

Extensions are created here WITHOUT binding to any specific Flask app.
They are initialized in create_app() using the app factory pattern.
This prevents circular imports and makes testing easier.
"""

from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient

# Global extension instances (unbound until init_app() is called)
jwt = JWTManager()
cors = CORS()

# PyMongo client — initialized in create_app()
mongo_client: MongoClient | None = None
db = None  # The specific database object (e.g., mongo_client["stylesense"])
