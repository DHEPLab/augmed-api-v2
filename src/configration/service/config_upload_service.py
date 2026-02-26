import json
import uuid
from io import StringIO
from typing import List, Optional

from src import db
from src.user.model.display_config import DisplayConfig
from src.user.utils.csv_parser import parse_csv_stream_to_configurations


def _generate_config_id(user_email: str, case_id: int, path_config) -> str:
    unique_string = f"{user_email}-{case_id}-{json.dumps(path_config)}"
    return uuid.uuid5(uuid.NAMESPACE_URL, unique_string).hex


class ConfigUploadService:

    def preview_csv(self, file_stream: StringIO) -> dict:
        """Parse CSV and return summary without writing to DB."""
        configs = parse_csv_stream_to_configurations(file_stream)
        return {
            "configs": [c.to_dict() for c in configs],
            "total": len(configs),
            "users": list({c.user_email for c in configs}),
            "cases": list({c.case_id for c in configs}),
        }

    def process_csv(
        self,
        file_stream: StringIO,
        experiment_id: Optional[str] = None,
        arm: Optional[str] = None,
        policy_id: Optional[str] = None,
    ) -> dict:
        """Parse CSV → DisplayConfig objects → upsert to DB.

        Metadata from form fields overrides CSV column values when both are present.
        """
        configs = parse_csv_stream_to_configurations(file_stream)

        results = []
        created = 0
        updated = 0

        for config in configs:
            # Form-level metadata overrides CSV-level metadata
            if experiment_id:
                config.experiment_id = experiment_id
            if arm:
                config.arm = arm
            if policy_id:
                config.policy_id = policy_id

            config.id = _generate_config_id(
                config.user_email, config.case_id, config.path_config
            )

            # Upsert: update if exists, insert if new
            existing = db.session.get(DisplayConfig, config.id)
            if existing:
                existing.path_config = config.path_config
                existing.experiment_id = config.experiment_id
                existing.arm = config.arm
                existing.policy_id = config.policy_id
                existing.rl_run_id = config.rl_run_id
                updated += 1
                status = "updated"
            else:
                db.session.add(config)
                created += 1
                status = "created"

            results.append({
                "user_email": config.user_email,
                "case_id": config.case_id,
                "status": status,
            })

        db.session.commit()

        return {
            "results": results,
            "summary": {
                "total": len(results),
                "created": created,
                "updated": updated,
            },
        }
