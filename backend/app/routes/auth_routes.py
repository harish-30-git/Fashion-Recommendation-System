"""
Authentication Routes for StyleSense.

Endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me (Protected with JWT)
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

import app.extensions as ext
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)


def _get_auth_service() -> AuthService:
    return AuthService(UserRepository(ext.db))


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return error_response("INVALID_JSON", "Request body must be valid JSON.", 400)

    service = _get_auth_service()
    result, error = service.register(data)
    if error:
        return error_response("REGISTRATION_FAILED", error, 400)

    return success_response(
        data=result,
        message="User registered successfully.",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return error_response("INVALID_JSON", "Request body must be valid JSON.", 400)

    service = _get_auth_service()
    result, error = service.login(data)
    if error:
        return error_response("LOGIN_FAILED", error, 401)

    return success_response(
        data=result,
        message="Login successful.",
        status_code=200,
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    service = _get_auth_service()
    user = service.get_current_user(user_id)

    if not user:
        return error_response("USER_NOT_FOUND", "User profile not found.", 404)

    return success_response(
        data={"user": user},
        message="Profile retrieved.",
        status_code=200,
    )
