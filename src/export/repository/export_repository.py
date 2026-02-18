from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class ExportRepository:
    """
    Read-only repository for exporting data.

    Uses raw SQL for complex joins across OMOP tables,
    matching the logic in script/answer_export/export_answers_to_csv.py.
    """

    AI_OBS_CONCEPT_ID = 45614722

    def __init__(self, session: Session):
        self.session = session

    def get_answers(
        self,
        limit: int = 1000,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> list[dict]:
        """Export answer data with OMOP joins for demographics, AI scores, and timing."""
        params = {
            "ai_concept": self.AI_OBS_CONCEPT_ID,
            "limit": limit,
            "offset": offset,
        }

        since_clause = ""
        if since:
            since_clause = "AND a.created_timestamp >= :since"
            params["since"] = since

        sql = text(f"""
            SELECT
                a.id AS answer_id,
                a.case_id,
                a.user_email,
                a.answer,
                a.display_configuration,
                a.ai_score_shown,
                a.answer_config_id,
                a.created_timestamp AS answer_created_at,
                v.person_id,
                v.visit_start_date,
                p.year_of_birth,
                g.concept_name AS gender_name,
                (
                    SELECT o.value_as_string
                    FROM observation o
                    WHERE o.visit_occurrence_id = a.case_id
                      AND o.observation_concept_id = :ai_concept
                    ORDER BY o.observation_datetime NULLS LAST, o.observation_id DESC
                    LIMIT 1
                ) AS ai_value_as_string,
                an.case_open_time,
                an.answer_open_time,
                an.answer_submit_time,
                an.to_answer_open_secs,
                an.to_submit_secs,
                an.total_duration_secs,
                ROW_NUMBER() OVER (PARTITION BY a.user_email ORDER BY a.id ASC) AS order_id
            FROM answer a
            LEFT JOIN visit_occurrence v ON v.visit_occurrence_id = a.case_id
            LEFT JOIN person p ON p.person_id = v.person_id
            LEFT JOIN concept g ON g.concept_id = p.gender_concept_id
            LEFT JOIN analytics an ON an.user_email = a.user_email
                AND an.case_id = a.case_id
            WHERE 1=1
            {since_clause}
            ORDER BY a.user_email, a.id ASC
            LIMIT :limit OFFSET :offset
        """)

        result = self.session.execute(sql, params)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def count_answers(self, since: Optional[datetime] = None) -> int:
        """Count total answers for pagination metadata."""
        params = {}
        since_clause = ""
        if since:
            since_clause = "WHERE a.created_timestamp >= :since"
            params["since"] = since

        sql = text(f"SELECT COUNT(*) FROM answer a {since_clause}")
        return self.session.execute(sql, params).scalar()

    def get_display_configs(
        self,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict]:
        """Export display config assignments."""
        sql = text("""
            SELECT
                dc.id AS config_id,
                dc.user_email,
                dc.case_id,
                dc.path_config,
                v.person_id,
                v.visit_start_date
            FROM display_config dc
            LEFT JOIN visit_occurrence v ON v.visit_occurrence_id = dc.case_id
            ORDER BY dc.user_email, dc.case_id
            LIMIT :limit OFFSET :offset
        """)
        result = self.session.execute(sql, {"limit": limit, "offset": offset})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def count_display_configs(self) -> int:
        sql = text("SELECT COUNT(*) FROM display_config")
        return self.session.execute(sql).scalar()

    def get_analytics(
        self,
        limit: int = 1000,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> list[dict]:
        """Export timing analytics."""
        params = {"limit": limit, "offset": offset}
        since_clause = ""
        if since:
            since_clause = "WHERE an.created_timestamp >= :since"
            params["since"] = since

        sql = text(f"""
            SELECT
                an.id AS analytics_id,
                an.user_email,
                an.case_config_id,
                an.case_id,
                an.case_open_time,
                an.answer_open_time,
                an.answer_submit_time,
                an.to_answer_open_secs,
                an.to_submit_secs,
                an.total_duration_secs,
                an.created_timestamp AS analytics_created_at
            FROM analytics an
            {since_clause}
            ORDER BY an.user_email, an.case_id
            LIMIT :limit OFFSET :offset
        """)
        result = self.session.execute(sql, params)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def count_analytics(self, since: Optional[datetime] = None) -> int:
        params = {}
        since_clause = ""
        if since:
            since_clause = "WHERE an.created_timestamp >= :since"
            params["since"] = since
        sql = text(f"SELECT COUNT(*) FROM analytics an {since_clause}")
        return self.session.execute(sql, params).scalar()

    def get_participants(
        self,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict]:
        """Export anonymized participant metadata with completion stats."""
        sql = text("""
            SELECT
                u.id AS user_id,
                u.position,
                u.employer,
                u.area_of_clinical_ex,
                u.active,
                u.admin_flag,
                u.created_timestamp AS user_created_at,
                (SELECT COUNT(*) FROM answer a WHERE a.user_email = u.email) AS cases_completed,
                (SELECT COUNT(*) FROM display_config dc WHERE dc.user_email = u.email) AS cases_assigned
            FROM "user" u
            WHERE u.admin_flag = false
            ORDER BY u.id
            LIMIT :limit OFFSET :offset
        """)
        result = self.session.execute(sql, {"limit": limit, "offset": offset})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def count_participants(self) -> int:
        sql = text('SELECT COUNT(*) FROM "user" WHERE admin_flag = false')
        return self.session.execute(sql).scalar()
