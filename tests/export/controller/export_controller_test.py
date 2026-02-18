import json
import os

import pytest


VALID_API_KEY = "test-export-key"


@pytest.fixture(autouse=True)
def set_export_api_key(monkeypatch):
    monkeypatch.setenv("EXPORT_API_KEY", VALID_API_KEY)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": VALID_API_KEY}


@pytest.fixture
def mock_answer_data():
    return {
        "data": [
            {
                "answer_id": 1,
                "case_id": 101,
                "user_email": "test@example.com",
                "answer": {"question": "answer"},
                "ai_score_shown": True,
                "person_id": 1001,
                "order_id": 1,
            }
        ],
        "pagination": {
            "total": 1,
            "limit": 1000,
            "offset": 0,
            "has_more": False,
        },
    }


# --- Authentication tests ---


def test_export_answers_requires_api_key(client):
    response = client.get("/api/v1/export/answers")
    assert response.status_code == 401


def test_export_answers_rejects_invalid_key(client):
    response = client.get(
        "/api/v1/export/answers",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_export_answers_no_configured_key(client, monkeypatch):
    monkeypatch.delenv("EXPORT_API_KEY", raising=False)
    response = client.get(
        "/api/v1/export/answers",
        headers={"X-API-Key": "any-key"},
    )
    assert response.status_code == 500


# --- Answers endpoint ---


def test_export_answers_json(client, mocker, auth_headers, mock_answer_data):
    mocker.patch(
        "src.export.service.export_service.ExportService.export_answers",
        return_value=mock_answer_data,
    )

    response = client.get(
        "/api/v1/export/answers",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) == 1


def test_export_answers_csv(client, mocker, auth_headers, mock_answer_data):
    mocker.patch(
        "src.export.service.export_service.ExportService.export_answers",
        return_value=mock_answer_data,
    )
    mocker.patch(
        "src.export.service.export_service.ExportService.rows_to_csv",
        return_value="answer_id,case_id\n1,101\n",
    )

    response = client.get(
        "/api/v1/export/answers",
        headers={**auth_headers, "Accept": "text/csv"},
    )
    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"
    assert "answer_id" in response.data.decode()


def test_export_answers_with_pagination(client, mocker, auth_headers, mock_answer_data):
    mocker.patch(
        "src.export.service.export_service.ExportService.export_answers",
        return_value=mock_answer_data,
    )

    response = client.get(
        "/api/v1/export/answers?limit=50&offset=10",
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_export_answers_with_since(client, mocker, auth_headers, mock_answer_data):
    mocker.patch(
        "src.export.service.export_service.ExportService.export_answers",
        return_value=mock_answer_data,
    )

    response = client.get(
        "/api/v1/export/answers?since=2024-01-01T00:00:00",
        headers=auth_headers,
    )
    assert response.status_code == 200


# --- Display configs endpoint ---


def test_export_display_configs(client, mocker, auth_headers):
    mock_data = {
        "data": [
            {
                "config_id": "abc123",
                "user_email": "test@example.com",
                "case_id": 101,
                "path_config": [{"path": "BACKGROUND.Medical History.Diabetes: Yes"}],
            }
        ],
        "pagination": {"total": 1, "limit": 1000, "offset": 0, "has_more": False},
    }
    mocker.patch(
        "src.export.service.export_service.ExportService.export_display_configs",
        return_value=mock_data,
    )

    response = client.get(
        "/api/v1/export/display-configs",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["data"]) == 1


# --- Analytics endpoint ---


def test_export_analytics(client, mocker, auth_headers):
    mock_data = {
        "data": [
            {
                "analytics_id": 1,
                "user_email": "test@example.com",
                "case_id": 101,
                "to_answer_open_secs": 30.5,
                "total_duration_secs": 120.0,
            }
        ],
        "pagination": {"total": 1, "limit": 1000, "offset": 0, "has_more": False},
    }
    mocker.patch(
        "src.export.service.export_service.ExportService.export_analytics",
        return_value=mock_data,
    )

    response = client.get(
        "/api/v1/export/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200


# --- Participants endpoint ---


def test_export_participants(client, mocker, auth_headers):
    mock_data = {
        "data": [
            {
                "user_id": 1,
                "position": "MD",
                "active": True,
                "cases_completed": 50,
                "cases_assigned": 100,
            }
        ],
        "pagination": {"total": 1, "limit": 1000, "offset": 0, "has_more": False},
    }
    mocker.patch(
        "src.export.service.export_service.ExportService.export_participants",
        return_value=mock_data,
    )

    response = client.get(
        "/api/v1/export/participants",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["data"][0]["cases_completed"] == 50
