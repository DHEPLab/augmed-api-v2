from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from sqlalchemy.dialects.postgresql import JSONB

from src import db


class RlRun(db.Model):
    __tablename__ = "rl_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(
        String(100),
        ForeignKey("experiment.experiment_id"),
        nullable=False,
    )
    model_version = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    triggered_by = Column(String(50), nullable=True)
    configs_generated = Column(Integer, nullable=True)
    answers_consumed = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    run_params = Column(JSONB, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "model_version": self.model_version,
            "status": self.status,
            "triggered_by": self.triggered_by,
            "configs_generated": self.configs_generated,
            "answers_consumed": self.answers_consumed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "run_params": self.run_params,
        }
