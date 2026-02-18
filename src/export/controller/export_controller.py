import json
import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, Response, jsonify, request

from src import db
from src.common.model.ApiResponse import ApiResponse
from src.common.model.ErrorCode import ErrorCode
from src.export.repository.export_repository import ExportRepository
from src.export.service.export_service import ExportService

export_blueprint = Blueprint("export", __name__)


def api_key_required():
    """Decorator for API key or JWT authentication.

    Accepts either:
    - X-API-Key header (service-to-service)
    - Authorization: Bearer <jwt> header (admin panel)
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Try API key first
            api_key = request.headers.get("X-API-Key")
            expected_key = os.getenv("EXPORT_API_KEY")

            if api_key and expected_key and api_key == expected_key:
                return fn(*args, **kwargs)

            # Fall back to JWT auth
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    from flask_jwt_extended import verify_jwt_in_request
                    verify_jwt_in_request()
                    return fn(*args, **kwargs)
                except Exception:
                    pass

            # Neither auth method succeeded
            if not expected_key:
                return (
                    jsonify(ApiResponse.fail(ErrorCode.INTERNAL_ERROR, "Export API key not configured")),
                    500,
                )

            return (
                jsonify(ApiResponse.fail(ErrorCode.UNAUTHORIZED, "Invalid or missing API key")),
                401,
            )

        return wrapper

    return decorator


def _get_export_service() -> ExportService:
    return ExportService(ExportRepository(db.session))


def _parse_pagination(req) -> tuple[int, int]:
    limit = min(int(req.args.get("limit", 1000)), 10000)
    offset = max(int(req.args.get("offset", 0)), 0)
    return limit, offset


def _parse_since(req) -> datetime | None:
    since_str = req.args.get("since")
    if since_str:
        return datetime.fromisoformat(since_str)
    return None


def _respond(result: dict, req):
    """Return JSON or CSV based on Accept header."""
    accept = req.headers.get("Accept", "application/json")

    if "text/csv" in accept:
        service = _get_export_service()
        csv_data = service.rows_to_csv(result["data"])
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )

    # Serialize datetimes in JSON response
    return Response(
        json.dumps(result, default=str),
        mimetype="application/json",
    )


@export_blueprint.route("/answers", methods=["GET"])
@api_key_required()
def export_answers():
    """Export answer data with OMOP demographics, AI scores, and timing."""
    limit, offset = _parse_pagination(request)
    since = _parse_since(request)
    service = _get_export_service()
    result = service.export_answers(limit=limit, offset=offset, since=since)
    return _respond(result, request)


@export_blueprint.route("/display-configs", methods=["GET"])
@api_key_required()
def export_display_configs():
    """Export current case assignments (display configurations)."""
    limit, offset = _parse_pagination(request)
    service = _get_export_service()
    result = service.export_display_configs(limit=limit, offset=offset)
    return _respond(result, request)


@export_blueprint.route("/analytics", methods=["GET"])
@api_key_required()
def export_analytics():
    """Export timing analytics."""
    limit, offset = _parse_pagination(request)
    since = _parse_since(request)
    service = _get_export_service()
    result = service.export_analytics(limit=limit, offset=offset, since=since)
    return _respond(result, request)


@export_blueprint.route("/participants", methods=["GET"])
@api_key_required()
def export_participants():
    """Export anonymized participant metadata with completion stats."""
    limit, offset = _parse_pagination(request)
    service = _get_export_service()
    result = service.export_participants(limit=limit, offset=offset)
    return _respond(result, request)
