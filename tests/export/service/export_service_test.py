from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.export.service.export_service import ExportService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return ExportService(export_repository=mock_repo)


def test_export_answers_returns_paginated_response(service, mock_repo):
    mock_repo.get_answers.return_value = [
        {"answer_id": 1, "case_id": 101},
        {"answer_id": 2, "case_id": 102},
    ]
    mock_repo.count_answers.return_value = 50

    result = service.export_answers(limit=10, offset=0)

    assert len(result["data"]) == 2
    assert result["pagination"]["total"] == 50
    assert result["pagination"]["limit"] == 10
    assert result["pagination"]["offset"] == 0
    assert result["pagination"]["has_more"] is True

    mock_repo.get_answers.assert_called_once_with(limit=10, offset=0, since=None)


def test_export_answers_with_since_filter(service, mock_repo):
    since = datetime(2024, 1, 1)
    mock_repo.get_answers.return_value = []
    mock_repo.count_answers.return_value = 0

    result = service.export_answers(limit=100, offset=0, since=since)

    mock_repo.get_answers.assert_called_once_with(limit=100, offset=0, since=since)
    mock_repo.count_answers.assert_called_once_with(since=since)
    assert result["pagination"]["has_more"] is False


def test_export_display_configs(service, mock_repo):
    mock_repo.get_display_configs.return_value = [
        {"config_id": "abc", "user_email": "test@example.com", "case_id": 101}
    ]
    mock_repo.count_display_configs.return_value = 1

    result = service.export_display_configs(limit=1000, offset=0)

    assert len(result["data"]) == 1
    assert result["pagination"]["total"] == 1


def test_export_analytics(service, mock_repo):
    mock_repo.get_analytics.return_value = []
    mock_repo.count_analytics.return_value = 0

    result = service.export_analytics(limit=100, offset=0)

    assert result["data"] == []
    assert result["pagination"]["total"] == 0


def test_export_participants(service, mock_repo):
    mock_repo.get_participants.return_value = [
        {"user_id": 1, "cases_completed": 50, "cases_assigned": 100}
    ]
    mock_repo.count_participants.return_value = 1

    result = service.export_participants()

    assert result["data"][0]["cases_completed"] == 50


def test_rows_to_csv_empty():
    assert ExportService.rows_to_csv([]) == ""


def test_rows_to_csv_with_data():
    rows = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    csv_str = ExportService.rows_to_csv(rows)
    assert "id,name" in csv_str
    assert "1,Alice" in csv_str
    assert "2,Bob" in csv_str


def test_rows_to_csv_serializes_datetime():
    rows = [
        {"id": 1, "created": datetime(2024, 1, 15, 10, 30, 0)},
    ]
    csv_str = ExportService.rows_to_csv(rows)
    assert "2024-01-15T10:30:00" in csv_str


def test_rows_to_csv_serializes_json_objects():
    rows = [
        {"id": 1, "config": {"path": "BACKGROUND.Medical History.Diabetes"}},
    ]
    csv_str = ExportService.rows_to_csv(rows)
    assert "BACKGROUND.Medical History.Diabetes" in csv_str


def test_has_more_false_when_no_more_data(service, mock_repo):
    mock_repo.get_answers.return_value = [{"id": 1}]
    mock_repo.count_answers.return_value = 1

    result = service.export_answers(limit=1000, offset=0)
    assert result["pagination"]["has_more"] is False


def test_has_more_true_when_more_data(service, mock_repo):
    mock_repo.get_answers.return_value = [{"id": i} for i in range(10)]
    mock_repo.count_answers.return_value = 100

    result = service.export_answers(limit=10, offset=0)
    assert result["pagination"]["has_more"] is True
