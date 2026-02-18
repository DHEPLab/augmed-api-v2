from unittest.mock import MagicMock, patch

import pytest

from src.experiment.model.experiment import Experiment
from src.experiment.model.rl_run import RlRun
from src.experiment.service.experiment_service import (
    ExperimentNotFoundError,
    ExperimentService,
    InvalidExperimentStateError,
)


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return ExperimentService(experiment_repository=mock_repo)


def _make_experiment(experiment_id="exp-abc123", name="Test Experiment",
                     status="active", arms=None):
    exp = Experiment(
        experiment_id=experiment_id,
        name=name,
        status=status,
        arms=arms or [{"name": "control"}, {"name": "treatment"}],
    )
    exp.id = 1
    return exp


def _make_rl_run(experiment_id="exp-abc123", status="pending"):
    run = RlRun(experiment_id=experiment_id, status=status, triggered_by="manual")
    run.id = 1
    return run


# --- create_experiment ---

def test_create_experiment(service, mock_repo):
    mock_repo.create_experiment.return_value = _make_experiment()

    result = service.create_experiment(
        name="Test Experiment",
        arms=[{"name": "control"}, {"name": "treatment"}],
    )

    assert result["name"] == "Test Experiment"
    assert result["experiment_id"] == "exp-abc123"
    mock_repo.create_experiment.assert_called_once()


def test_create_experiment_generates_unique_id(service, mock_repo):
    mock_repo.create_experiment.side_effect = lambda exp: exp

    with patch("src.experiment.service.experiment_service.uuid") as mock_uuid:
        mock_uuid.uuid4.return_value.hex = "deadbeef1234567890ab"
        service.create_experiment(name="Test", arms=[{"name": "a"}])

    call_args = mock_repo.create_experiment.call_args[0][0]
    assert call_args.experiment_id == "exp-deadbeef1234"


# --- get_experiment ---

def test_get_experiment_returns_with_runs(service, mock_repo):
    exp = _make_experiment()
    mock_repo.get_experiment_by_id.return_value = exp
    mock_repo.get_rl_runs_for_experiment.return_value = [_make_rl_run()]

    result = service.get_experiment("exp-abc123")

    assert result["experiment_id"] == "exp-abc123"
    assert len(result["runs"]) == 1


def test_get_experiment_not_found(service, mock_repo):
    mock_repo.get_experiment_by_id.return_value = None

    with pytest.raises(ExperimentNotFoundError):
        service.get_experiment("exp-nonexistent")


# --- list_experiments ---

def test_list_experiments(service, mock_repo):
    mock_repo.list_experiments.return_value = [_make_experiment()]

    result = service.list_experiments()

    assert len(result) == 1
    mock_repo.list_experiments.assert_called_once_with(status=None)


def test_list_experiments_with_status_filter(service, mock_repo):
    mock_repo.list_experiments.return_value = []

    service.list_experiments(status="active")

    mock_repo.list_experiments.assert_called_once_with(status="active")


# --- update_experiment_status ---

def test_update_experiment_status(service, mock_repo):
    exp = _make_experiment()
    mock_repo.get_experiment_by_id.return_value = exp
    mock_repo.update_experiment.return_value = exp

    result = service.update_experiment_status("exp-abc123", "paused")

    assert exp.status == "paused"
    mock_repo.update_experiment.assert_called_once()


def test_update_experiment_status_invalid(service, mock_repo):
    with pytest.raises(InvalidExperimentStateError, match="Invalid status"):
        service.update_experiment_status("exp-abc123", "invalid_status")


def test_update_experiment_status_not_found(service, mock_repo):
    mock_repo.get_experiment_by_id.return_value = None

    with pytest.raises(ExperimentNotFoundError):
        service.update_experiment_status("exp-nonexistent", "paused")


# --- create_rl_run ---

def test_create_rl_run(service, mock_repo):
    exp = _make_experiment(status="active")
    mock_repo.get_experiment_by_id.return_value = exp
    mock_repo.create_rl_run.return_value = _make_rl_run()

    result = service.create_rl_run("exp-abc123")

    assert result["experiment_id"] == "exp-abc123"
    mock_repo.create_rl_run.assert_called_once()


def test_create_rl_run_experiment_not_found(service, mock_repo):
    mock_repo.get_experiment_by_id.return_value = None

    with pytest.raises(ExperimentNotFoundError):
        service.create_rl_run("exp-nonexistent")


def test_create_rl_run_experiment_not_active(service, mock_repo):
    exp = _make_experiment(status="paused")
    mock_repo.get_experiment_by_id.return_value = exp

    with pytest.raises(InvalidExperimentStateError, match="paused"):
        service.create_rl_run("exp-abc123")


# --- get_rl_runs ---

def test_get_rl_runs(service, mock_repo):
    mock_repo.get_experiment_by_id.return_value = _make_experiment()
    mock_repo.get_rl_runs_for_experiment.return_value = [_make_rl_run()]

    result = service.get_rl_runs("exp-abc123")

    assert len(result) == 1


def test_get_rl_runs_experiment_not_found(service, mock_repo):
    mock_repo.get_experiment_by_id.return_value = None

    with pytest.raises(ExperimentNotFoundError):
        service.get_rl_runs("exp-nonexistent")
