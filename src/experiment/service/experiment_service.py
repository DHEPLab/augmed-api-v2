import uuid

from src.experiment.model.experiment import Experiment
from src.experiment.model.rl_run import RlRun
from src.experiment.repository.experiment_repository import ExperimentRepository


class ExperimentNotFoundError(Exception):
    pass


class InvalidExperimentStateError(Exception):
    pass


class ExperimentService:
    def __init__(self, experiment_repository: ExperimentRepository):
        self.repo = experiment_repository

    def create_experiment(self, name: str, arms: list, description: str | None = None,
                          case_pool: list | None = None) -> dict:
        experiment_id = f"exp-{uuid.uuid4().hex[:12]}"
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            arms=arms,
            description=description,
            case_pool=case_pool,
        )
        created = self.repo.create_experiment(experiment)
        return created.to_dict()

    def get_experiment(self, experiment_id: str) -> dict:
        experiment = self.repo.get_experiment_by_id(experiment_id)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment '{experiment_id}' not found")
        result = experiment.to_dict()
        runs = self.repo.get_rl_runs_for_experiment(experiment_id)
        result["runs"] = [r.to_dict() for r in runs]
        return result

    def list_experiments(self, status: str | None = None) -> list[dict]:
        experiments = self.repo.list_experiments(status=status)
        return [e.to_dict() for e in experiments]

    def update_experiment_status(self, experiment_id: str, status: str) -> dict:
        valid_statuses = {"active", "paused", "completed", "archived"}
        if status not in valid_statuses:
            raise InvalidExperimentStateError(
                f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
            )
        experiment = self.repo.get_experiment_by_id(experiment_id)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment '{experiment_id}' not found")
        experiment.status = status
        self.repo.update_experiment(experiment)
        return experiment.to_dict()

    def create_rl_run(self, experiment_id: str, triggered_by: str = "manual",
                      run_params: dict | None = None) -> dict:
        experiment = self.repo.get_experiment_by_id(experiment_id)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment '{experiment_id}' not found")
        if experiment.status != "active":
            raise InvalidExperimentStateError(
                f"Cannot create run for experiment in '{experiment.status}' status"
            )
        rl_run = RlRun(
            experiment_id=experiment_id,
            triggered_by=triggered_by,
            run_params=run_params,
        )
        created = self.repo.create_rl_run(rl_run)
        return created.to_dict()

    def get_rl_runs(self, experiment_id: str) -> list[dict]:
        experiment = self.repo.get_experiment_by_id(experiment_id)
        if not experiment:
            raise ExperimentNotFoundError(f"Experiment '{experiment_id}' not found")
        runs = self.repo.get_rl_runs_for_experiment(experiment_id)
        return [r.to_dict() for r in runs]
