from src.experiment.model.experiment import Experiment
from src.experiment.model.rl_run import RlRun


class ExperimentRepository:
    def __init__(self, session):
        self.session = session

    def create_experiment(self, experiment: Experiment) -> Experiment:
        self.session.add(experiment)
        self.session.commit()
        return experiment

    def get_experiment_by_id(self, experiment_id: str) -> Experiment | None:
        return self.session.query(Experiment).filter_by(experiment_id=experiment_id).first()

    def list_experiments(self, status: str | None = None) -> list[Experiment]:
        query = self.session.query(Experiment)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Experiment.created_at.desc()).all()

    def update_experiment(self, experiment: Experiment) -> Experiment:
        self.session.commit()
        return experiment

    def create_rl_run(self, rl_run: RlRun) -> RlRun:
        self.session.add(rl_run)
        self.session.commit()
        return rl_run

    def get_rl_runs_for_experiment(self, experiment_id: str) -> list[RlRun]:
        return (
            self.session.query(RlRun)
            .filter_by(experiment_id=experiment_id)
            .order_by(RlRun.id.desc())
            .all()
        )

    def get_rl_run_by_id(self, run_id: int) -> RlRun | None:
        return self.session.query(RlRun).filter_by(id=run_id).first()

    def update_rl_run(self, rl_run: RlRun) -> RlRun:
        self.session.commit()
        return rl_run
