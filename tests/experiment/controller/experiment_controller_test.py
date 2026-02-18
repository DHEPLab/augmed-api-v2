import json

import pytest

VALID_API_KEY = "test-export-key"


@pytest.fixture(autouse=True)
def set_export_api_key(monkeypatch):
    monkeypatch.setenv("EXPORT_API_KEY", VALID_API_KEY)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": VALID_API_KEY, "Content-Type": "application/json"}


@pytest.fixture
def mock_experiment():
    return {
        "id": 1,
        "experiment_id": "exp-abc123",
        "name": "Test Experiment",
        "description": "A test",
        "status": "active",
        "arms": [{"name": "control"}, {"name": "treatment"}],
        "case_pool": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


@pytest.fixture
def mock_rl_run():
    return {
        "id": 1,
        "experiment_id": "exp-abc123",
        "model_version": None,
        "status": "pending",
        "triggered_by": "manual",
        "configs_generated": None,
        "answers_consumed": None,
        "started_at": None,
        "completed_at": None,
        "run_params": None,
    }


# --- Authentication ---

def test_experiment_requires_api_key(client):
    response = client.post("/api/v1/experiments")
    assert response.status_code == 401


# --- Create experiment ---

def test_create_experiment(client, mocker, auth_headers, mock_experiment):
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.create_experiment",
        return_value=mock_experiment,
    )

    response = client.post(
        "/api/v1/experiments",
        headers=auth_headers,
        data=json.dumps({
            "name": "Test Experiment",
            "arms": [{"name": "control"}, {"name": "treatment"}],
        }),
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["data"]["experiment_id"] == "exp-abc123"


def test_create_experiment_missing_fields(client, auth_headers):
    response = client.post(
        "/api/v1/experiments",
        headers=auth_headers,
        data=json.dumps({"name": "No arms"}),
    )
    assert response.status_code == 400


def test_create_experiment_no_body(client, auth_headers):
    response = client.post(
        "/api/v1/experiments",
        headers=auth_headers,
        data=json.dumps(None),
    )
    assert response.status_code == 400


# --- List experiments ---

def test_list_experiments(client, mocker, auth_headers, mock_experiment):
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.list_experiments",
        return_value=[mock_experiment],
    )

    response = client.get("/api/v1/experiments", headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["data"]["experiments"]) == 1


def test_list_experiments_with_status_filter(client, mocker, auth_headers):
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.list_experiments",
        return_value=[],
    )

    response = client.get("/api/v1/experiments?status=active", headers=auth_headers)
    assert response.status_code == 200


# --- Get experiment ---

def test_get_experiment(client, mocker, auth_headers, mock_experiment):
    mock_experiment["runs"] = []
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.get_experiment",
        return_value=mock_experiment,
    )

    response = client.get("/api/v1/experiments/exp-abc123", headers=auth_headers)
    assert response.status_code == 200


def test_get_experiment_not_found(client, mocker, auth_headers):
    from src.experiment.service.experiment_service import ExperimentNotFoundError

    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.get_experiment",
        side_effect=ExperimentNotFoundError("not found"),
    )

    response = client.get("/api/v1/experiments/exp-nonexistent", headers=auth_headers)
    assert response.status_code == 404


# --- Update experiment status ---

def test_update_experiment_status(client, mocker, auth_headers, mock_experiment):
    mock_experiment["status"] = "paused"
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.update_experiment_status",
        return_value=mock_experiment,
    )

    response = client.patch(
        "/api/v1/experiments/exp-abc123/status",
        headers=auth_headers,
        data=json.dumps({"status": "paused"}),
    )
    assert response.status_code == 200


def test_update_experiment_status_missing_body(client, auth_headers):
    response = client.patch(
        "/api/v1/experiments/exp-abc123/status",
        headers=auth_headers,
        data=json.dumps({}),
    )
    assert response.status_code == 400


def test_update_experiment_status_invalid(client, mocker, auth_headers):
    from src.experiment.service.experiment_service import InvalidExperimentStateError

    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.update_experiment_status",
        side_effect=InvalidExperimentStateError("Invalid status"),
    )

    response = client.patch(
        "/api/v1/experiments/exp-abc123/status",
        headers=auth_headers,
        data=json.dumps({"status": "bad"}),
    )
    assert response.status_code == 400


# --- RL runs ---

def test_create_rl_run(client, mocker, auth_headers, mock_rl_run):
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.create_rl_run",
        return_value=mock_rl_run,
    )

    response = client.post(
        "/api/v1/experiments/exp-abc123/runs",
        headers=auth_headers,
        data=json.dumps({"triggered_by": "manual"}),
    )
    assert response.status_code == 201


def test_list_rl_runs(client, mocker, auth_headers, mock_rl_run):
    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.get_rl_runs",
        return_value=[mock_rl_run],
    )

    response = client.get("/api/v1/experiments/exp-abc123/runs", headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["data"]["runs"]) == 1


def test_list_rl_runs_experiment_not_found(client, mocker, auth_headers):
    from src.experiment.service.experiment_service import ExperimentNotFoundError

    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.get_rl_runs",
        side_effect=ExperimentNotFoundError("not found"),
    )

    response = client.get("/api/v1/experiments/exp-nonexistent/runs", headers=auth_headers)
    assert response.status_code == 404


# --- Batch config endpoint ---

def test_batch_create_configs(client, mocker, auth_headers):
    mocker.patch("src.experiment.controller.experiment_controller.db")

    response = client.post(
        "/api/v1/configs/batch",
        headers=auth_headers,
        data=json.dumps({
            "configs": [
                {
                    "user_email": "test@example.com",
                    "case_id": 101,
                    "path_config": [{"path": "BACKGROUND.Medical History.Diabetes: Yes"}],
                    "experiment_id": "exp-abc123",
                    "arm": "treatment",
                }
            ]
        }),
    )
    assert response.status_code == 201


def test_batch_create_configs_missing_configs(client, auth_headers):
    response = client.post(
        "/api/v1/configs/batch",
        headers=auth_headers,
        data=json.dumps({}),
    )
    assert response.status_code == 400


def test_batch_create_configs_empty_array(client, auth_headers):
    response = client.post(
        "/api/v1/configs/batch",
        headers=auth_headers,
        data=json.dumps({"configs": []}),
    )
    assert response.status_code == 400


def test_batch_create_configs_missing_required_fields(client, mocker, auth_headers):
    mocker.patch("src.experiment.controller.experiment_controller.db")

    response = client.post(
        "/api/v1/configs/batch",
        headers=auth_headers,
        data=json.dumps({
            "configs": [
                {"user_email": "test@example.com"},
            ]
        }),
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["data"]["results"][0]["status"] == "failed"


def test_create_rl_run_experiment_not_found(client, mocker, auth_headers):
    from src.experiment.service.experiment_service import ExperimentNotFoundError

    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.create_rl_run",
        side_effect=ExperimentNotFoundError("not found"),
    )

    response = client.post(
        "/api/v1/experiments/exp-nonexistent/runs",
        headers=auth_headers,
        data=json.dumps({}),
    )
    assert response.status_code == 404


def test_create_rl_run_experiment_not_active(client, mocker, auth_headers):
    from src.experiment.service.experiment_service import InvalidExperimentStateError

    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.create_rl_run",
        side_effect=InvalidExperimentStateError("paused"),
    )

    response = client.post(
        "/api/v1/experiments/exp-abc123/runs",
        headers=auth_headers,
        data=json.dumps({}),
    )
    assert response.status_code == 400


def test_update_experiment_status_not_found(client, mocker, auth_headers):
    from src.experiment.service.experiment_service import ExperimentNotFoundError

    mocker.patch(
        "src.experiment.service.experiment_service.ExperimentService.update_experiment_status",
        side_effect=ExperimentNotFoundError("not found"),
    )

    response = client.patch(
        "/api/v1/experiments/exp-nonexistent/status",
        headers=auth_headers,
        data=json.dumps({"status": "paused"}),
    )
    assert response.status_code == 404


def test_batch_create_configs_db_error(client, mocker, auth_headers):
    mock_db = mocker.patch("src.experiment.controller.experiment_controller.db")
    mock_db.session.flush.side_effect = Exception("DB error")

    response = client.post(
        "/api/v1/configs/batch",
        headers=auth_headers,
        data=json.dumps({
            "configs": [
                {"user_email": "test@example.com", "case_id": 101}
            ]
        }),
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["data"]["results"][0]["status"] == "failed"
