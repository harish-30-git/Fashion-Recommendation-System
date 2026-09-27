"""
Interaction Tracking Routes for StyleSense.

Endpoints:
  POST /api/interactions
  GET  /api/interactions/history
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

import app.extensions as ext
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.product_repository import ProductRepository
from app.services.interaction_service import InteractionService
from app.utils.pagination import get_pagination_params
from app.utils.response import success_response, error_response

interaction_bp = Blueprint("interactions", __name__)


def _get_interaction_service() -> InteractionService:
    return InteractionService(
        interaction_repo=InteractionRepository(ext.db),
        product_repo=ProductRepository(ext.db),
        weights=current_app.config.get("INTERACTION_WEIGHTS"),
    )


@interaction_bp.route("", methods=["POST"])
@jwt_required()
def log_interaction():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data:
        return error_response("VALIDATION_ERROR", "Request body must be valid JSON.", 400)

    product_id = data.get("product_id")
    interaction_type = data.get("interaction_type")
    session_id = data.get("session_id")

    service = _get_interaction_service()
    doc, error = service.log(
        user_id=user_id,
        product_id=product_id,
        interaction_type=interaction_type,
        session_id=session_id,
    )

    if error:
        return error_response("INTERACTION_ERROR", error, 400)

    return success_response(
        data={"interaction": doc},
        message="Interaction logged.",
        status_code=201,
    )


@interaction_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    page, per_page = get_pagination_params(request)
    interaction_type = request.args.get("type")

    service = _get_interaction_service()
    items, pagination = service.get_history(
        user_id=user_id,
        interaction_type=interaction_type,
        page=page,
        per_page=per_page,
    )

    return success_response(
        data={"history": items},
        pagination=pagination,
        status_code=200,
    )
