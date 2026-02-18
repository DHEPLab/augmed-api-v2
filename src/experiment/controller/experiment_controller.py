from flask import Blueprint, jsonify, request

from src import db
from src.common.model.ApiResponse import ApiResponse
from src.common.model.ErrorCode import ErrorCode
from src.export.controller.export_controller import api_key_required
from src.experiment.repository.experiment_repository import ExperimentRepository
from src.experiment.service.experiment_service import (
    ExperimentNotFoundError,
    ExperimentService,
    InvalidExperimentStateError,
)
from src.user.model.display_config import DisplayConfig

experiment_blueprint = Blueprint("experiment", __name__)


def _get_experiment_service() -> ExperimentService:
    return ExperimentService(ExperimentRepository(db.session))


@experiment_blueprint.route("/experiments", methods=["POST"])
@api_key_required()
def create_experiment():
    body = request.get_json()
    if not body:
        return jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, "Request body required")), 400

    name = body.get("name")
    arms = body.get("arms")
    if not name or not arms:
        return (
            jsonify(ApiResponse.fail(ErrorCode.INVALID_PARAMETER, "'name' and 'arms' are required")),
            400,
        )

    service = _get_experiment_service()
    result = service.create_experiment(
        name=name,
        arms=arms,
        description=body.get("description"),
        case_pool=body.get("case_pool"),
    )
    return jsonify(ApiResponse.success(result)), 201


@experiment_blueprint.route("/experiments", methods=["GET"])
@api_key_required()
def list_experiments():
    status = request.args.get("status")
    service = _get_experiment_service()
    experiments = service.list_experiments(status=status)
    return jsonify(ApiResponse.success({"experiments": experiments})), 200


@experiment_blueprint.route("/experiments/<experiment_id>", methods=["GET"])
@api_key_required()
def get_experiment(experiment_id):
    service = _get_experiment_service()
    try:
        result = service.get_experiment(experiment_id)
    except ExperimentNotFoundError:
        return jsonify(ApiResponse.fail(ErrorCode.NOT_FOUND, "Experiment not found")), 404
    return jsonify(ApiResponse.success(result)), 200


@experiment_blueprint.route("/experiments/<experiment_id>/status", methods=["PATCH"])
@api_key_required()
def update_experiment_status(experiment_id):
    body = request.get_json()
    if not body or "status" not in body:
        return jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, "'status' is required")), 400

    service = _get_experiment_service()
    try:
        result = service.update_experiment_status(experiment_id, body["status"])
    except ExperimentNotFoundError:
        return jsonify(ApiResponse.fail(ErrorCode.NOT_FOUND, "Experiment not found")), 404
    except InvalidExperimentStateError as e:
        return jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, str(e))), 400
    return jsonify(ApiResponse.success(result)), 200


@experiment_blueprint.route("/experiments/<experiment_id>/runs", methods=["POST"])
@api_key_required()
def create_rl_run(experiment_id):
    body = request.get_json() or {}
    service = _get_experiment_service()
    try:
        result = service.create_rl_run(
            experiment_id=experiment_id,
            triggered_by=body.get("triggered_by", "manual"),
            run_params=body.get("run_params"),
        )
    except ExperimentNotFoundError:
        return jsonify(ApiResponse.fail(ErrorCode.NOT_FOUND, "Experiment not found")), 404
    except InvalidExperimentStateError as e:
        return jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, str(e))), 400
    return jsonify(ApiResponse.success(result)), 201


@experiment_blueprint.route("/experiments/<experiment_id>/runs", methods=["GET"])
@api_key_required()
def list_rl_runs(experiment_id):
    service = _get_experiment_service()
    try:
        runs = service.get_rl_runs(experiment_id)
    except ExperimentNotFoundError:
        return jsonify(ApiResponse.fail(ErrorCode.NOT_FOUND, "Experiment not found")), 404
    return jsonify(ApiResponse.success({"runs": runs})), 200


@experiment_blueprint.route("/configs/batch", methods=["POST"])
@api_key_required()
def batch_create_configs():
    body = request.get_json()
    if not body or "configs" not in body:
        return jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, "'configs' array is required")), 400

    configs = body["configs"]
    if not isinstance(configs, list) or len(configs) == 0:
        return jsonify(ApiResponse.fail(ErrorCode.BAD_REQUEST, "'configs' must be a non-empty array")), 400

    results = []
    for config_data in configs:
        user_email = config_data.get("user_email")
        case_id = config_data.get("case_id")
        if not user_email or case_id is None:
            results.append({"status": "failed", "error": "user_email and case_id required"})
            continue

        dc = DisplayConfig(
            user_email=user_email,
            case_id=case_id,
            path_config=config_data.get("path_config"),
            id=config_data.get("id"),
        )
        # Set experiment tracking fields if present
        if "experiment_id" in config_data:
            dc.experiment_id = config_data["experiment_id"]
        if "rl_run_id" in config_data:
            dc.rl_run_id = config_data["rl_run_id"]
        if "arm" in config_data:
            dc.arm = config_data["arm"]

        try:
            db.session.add(dc)
            db.session.flush()
            results.append({"status": "added", "user_email": user_email, "case_id": case_id})
        except Exception:
            db.session.rollback()
            results.append({"status": "failed", "user_email": user_email, "case_id": case_id})

    db.session.commit()
    return jsonify(ApiResponse.success({"results": results, "total": len(results)})), 201
