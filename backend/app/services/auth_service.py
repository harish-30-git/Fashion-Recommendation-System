"""
Authentication Service for StyleSense.

Handles:
  - User registration with bcrypt password hashing.
  - User login verification.
  - JWT token generation using Flask-JWT-Extended.
  - Profile retrieval with strict security (never exposing password hash).
"""

import bcrypt
from flask_jwt_extended import create_access_token

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.validators import validate_register, validate_login


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(self, data: dict) -> tuple[dict | None, str | None]:
        """
        Register a new user.

        Args:
            data: dict with email, username, password, full_name, and optional gender.

        Returns:
            (result_dict, error_message)
            result_dict contains {"user": safe_user_dict, "access_token": token_str}
        """
        is_valid, error = validate_register(data)
        if not is_valid:
            return None, error

        email = data["email"].lower().strip()
        username = data["username"].strip()

        if self.user_repo.email_exists(email):
            return None, "An account with this email already exists."

        if self.user_repo.username_exists(username):
            return None, "This username is already taken."

        # Bcrypt password hashing
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(data["password"].encode("utf-8"), salt).decode("utf-8")

        new_user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=data["full_name"].strip(),
            gender=data.get("gender", "Unisex"),
        )

        user_doc = self.user_repo.create(new_user)
        if not user_doc:
            return None, "Failed to create user account. Please try again."

        user_id_str = str(user_doc["_id"])
        access_token = create_access_token(identity=user_id_str)

        return {
            "user": User.from_mongo(user_doc),
            "access_token": access_token,
        }, None

    def login(self, data: dict) -> tuple[dict | None, str | None]:
        """
        Authenticate an existing user.

        Args:
            data: dict with email and password.

        Returns:
            (result_dict, error_message)
        """
        is_valid, error = validate_login(data)
        if not is_valid:
            return None, error

        email = data["email"].lower().strip()
        user_doc = self.user_repo.find_by_email(email)

        if not user_doc:
            return None, "Invalid email or password."

        stored_hash = user_doc.get("password_hash", "")
        # Constant-time password verification via bcrypt
        if not bcrypt.checkpw(data["password"].encode("utf-8"), stored_hash.encode("utf-8")):
            return None, "Invalid email or password."

        user_id_str = str(user_doc["_id"])
        access_token = create_access_token(identity=user_id_str)

        return {
            "user": User.from_mongo(user_doc),
            "access_token": access_token,
        }, None

    def get_current_user(self, user_id: str) -> dict | None:
        """
        Retrieve safe public profile for an authenticated user.
        """
        user_doc = self.user_repo.find_by_id(user_id)
        if not user_doc:
            return None
        return User.from_mongo(user_doc)
