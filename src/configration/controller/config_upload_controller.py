from io import StringIO

from flask import Blueprint, jsonify, request

from src.common.exception.BusinessException import BusinessException, BusinessExceptionEnum
from src.common.model.ApiResponse import ApiResponse
from src.common.model.ErrorCode import ErrorCode
from src.configration.service.config_upload_service import ConfigUploadService
from src.export.controller.export_controller import api_key_required
from src.user.utils.csv_parser import is_csv_file

# Admin blueprint — JWT-protected via Flask login (registered at /admin)
admin_config_upload_blueprint = Blueprint("admin_config_upload", __name__)

# API blueprint — API key or JWT (registered at /api/v1)
api_config_upload_blueprint = Blueprint("api_config_upload", __name__)


def _get_upload_service() -> ConfigUploadService:
    return ConfigUploadService()


def _validate_file():
    """Extract and validate the uploaded CSV file. Returns file stream."""
    if "file" not in request.files:
        return None, (
            jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, "No file part in the request")),
            400,
        )

    file = request.files["file"]
    if not is_csv_file(file.filename):
        return None, (
            jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, "Only .csv files are allowed")),
            400,
        )

    file_stream = StringIO(file.read().decode("utf-8"))
    return file_stream, None


def _extract_metadata():
    """Extract optional experiment metadata from form fields or query params."""
    experiment_id = request.form.get("experiment_id") or request.args.get("experiment_id")
    arm = request.form.get("arm") or request.args.get("arm")
    policy_id = request.form.get("policy_id") or request.args.get("policy_id")
    return experiment_id, arm, policy_id


def _handle_upload():
    """Shared upload logic for both admin and API endpoints."""
    file_stream, error = _validate_file()
    if error:
        return error

    experiment_id, arm, policy_id = _extract_metadata()
    service = _get_upload_service()

    try:
        result = service.process_csv(
            file_stream,
            experiment_id=experiment_id,
            arm=arm,
            policy_id=policy_id,
        )
    except BusinessException as e:
        return jsonify(ApiResponse.error(e)), 400

    return jsonify(ApiResponse.success(result)), 200


def _handle_preview():
    """Shared preview logic for both admin and API endpoints."""
    file_stream, error = _validate_file()
    if error:
        return error

    service = _get_upload_service()

    try:
        result = service.preview_csv(file_stream)
    except BusinessException as e:
        return jsonify(ApiResponse.error(e)), 400

    return jsonify(ApiResponse.success(result)), 200


# --- Admin endpoints (JWT auth via Flask session) ---

@admin_config_upload_blueprint.route("/config/upload", methods=["POST"])
def admin_upload_config():
    """Upload CSV of display config assignments (admin panel)."""
    return _handle_upload()


@admin_config_upload_blueprint.route("/config/upload/preview", methods=["POST"])
def admin_preview_config():
    """Preview CSV parsing without writing to DB (admin panel)."""
    return _handle_preview()


# --- API endpoints (API key or JWT auth) ---

@api_config_upload_blueprint.route("/config/upload", methods=["POST"])
@api_key_required()
def api_upload_config():
    """Upload CSV of display config assignments (programmatic access)."""
    return _handle_upload()


@api_config_upload_blueprint.route("/config/upload/preview", methods=["POST"])
@api_key_required()
def api_preview_config():
    """Preview CSV parsing without writing to DB (programmatic access)."""
    return _handle_preview()
