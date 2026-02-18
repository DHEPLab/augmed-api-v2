from src import db


class DisplayConfig(db.Model):
    __tablename__ = "display_config"
    id = db.Column(db.String, primary_key=True)
    user_email = db.Column(db.String)
    case_id = db.Column(db.Integer)
    path_config = db.Column(db.JSON, nullable=True)
    experiment_id = db.Column(db.String(100), nullable=True)
    rl_run_id = db.Column(db.Integer, nullable=True)
    arm = db.Column(db.String(100), nullable=True)

    def __init__(self, user_email, case_id, path_config=None, id=None,
                 experiment_id=None, rl_run_id=None, arm=None):
        self.user_email = user_email
        self.case_id = case_id
        self.path_config = path_config
        self.id = id
        self.experiment_id = experiment_id
        self.rl_run_id = rl_run_id
        self.arm = arm

    def to_dict(self):
        return {
            "user_email": self.user_email,
            "case_id": self.case_id,
            "path_config": self.path_config,
            "experiment_id": self.experiment_id,
            "rl_run_id": self.rl_run_id,
            "arm": self.arm,
        }
