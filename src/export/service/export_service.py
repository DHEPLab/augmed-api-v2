import csv
import io
from datetime import datetime
from typing import Optional

from src.export.repository.export_repository import ExportRepository


class ExportService:
    """
    Business logic for data export. Handles pagination metadata
    and CSV formatting.
    """

    def __init__(self, export_repository: ExportRepository):
        self.repo = export_repository

    def export_answers(
        self,
        limit: int = 1000,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> dict:
        rows = self.repo.get_answers(limit=limit, offset=offset, since=since)
        total = self.repo.count_answers(since=since)
        return self._paginated_response(rows, total, limit, offset)

    def export_display_configs(
        self,
        limit: int = 1000,
        offset: int = 0,
    ) -> dict:
        rows = self.repo.get_display_configs(limit=limit, offset=offset)
        total = self.repo.count_display_configs()
        return self._paginated_response(rows, total, limit, offset)

    def export_analytics(
        self,
        limit: int = 1000,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> dict:
        rows = self.repo.get_analytics(limit=limit, offset=offset, since=since)
        total = self.repo.count_analytics(since=since)
        return self._paginated_response(rows, total, limit, offset)

    def export_participants(
        self,
        limit: int = 1000,
        offset: int = 0,
    ) -> dict:
        rows = self.repo.get_participants(limit=limit, offset=offset)
        total = self.repo.count_participants()
        return self._paginated_response(rows, total, limit, offset)

    @staticmethod
    def rows_to_csv(rows: list[dict]) -> str:
        """Convert list of dicts to CSV string."""
        if not rows:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            # Serialize datetime and complex types
            cleaned = {}
            for k, v in row.items():
                if isinstance(v, datetime):
                    cleaned[k] = v.isoformat()
                elif isinstance(v, (dict, list)):
                    import json
                    cleaned[k] = json.dumps(v)
                else:
                    cleaned[k] = v
            writer.writerow(cleaned)
        return output.getvalue()

    @staticmethod
    def _paginated_response(
        rows: list[dict], total: int, limit: int, offset: int
    ) -> dict:
        return {
            "data": rows,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            },
        }
