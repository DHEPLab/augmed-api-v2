import csv
import json
import os
from io import BytesIO, StringIO

import pytest

VALID_API_KEY = "test-upload-key"


@pytest.fixture(autouse=True)
def set_export_api_key(monkeypatch):
    monkeypatch.setenv("EXPORT_API_KEY", VALID_API_KEY)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": VALID_API_KEY}


def _make_csv_bytes(rows):
    """Build a CSV file as bytes from a list of row-lists (first row = headers)."""
    stream = StringIO()
    writer = csv.writer(stream)
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _make_csv_file(rows, filename="test.csv"):
    """Create a (BytesIO, filename) tuple suitable for Flask test client file upload."""
    data = _make_csv_bytes(rows)
    return (BytesIO(data), filename)


# --- Admin upload endpoint tests ---


def test_admin_upload_no_file(client):
    response = client.post("/admin/config/upload")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] is not None


def test_admin_upload_non_csv(client):
    response = client.post(
        "/admin/config/upload",
        data={"file": (BytesIO(b"not csv"), "test.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_admin_upload_valid_csv(client):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["test@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
        ["test@example.com", "1001", "BACKGROUND.Medical History.Hypertension: Yes", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/admin/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["data"]["summary"]["total"] == 1
    assert data["data"]["summary"]["created"] == 1


def test_admin_upload_with_metadata(client):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["test@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/admin/config/upload",
        data={
            "file": _make_csv_file(csv_rows),
            "experiment_id": "eval_001",
            "arm": "learned_policy",
            "policy_id": "thompson_v1",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["data"]["summary"]["created"] == 1


def test_admin_upload_upsert_updates_existing(client):
    """Upload same CSV twice — second time should update, not create."""
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["test@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
    ]

    # First upload
    response1 = client.post(
        "/admin/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        content_type="multipart/form-data",
    )
    assert response1.status_code == 200
    data1 = json.loads(response1.data)
    assert data1["data"]["summary"]["created"] == 1
    assert data1["data"]["summary"]["updated"] == 0

    # Second upload (same data)
    response2 = client.post(
        "/admin/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        content_type="multipart/form-data",
    )
    assert response2.status_code == 200
    data2 = json.loads(response2.data)
    assert data2["data"]["summary"]["created"] == 0
    assert data2["data"]["summary"]["updated"] == 1


# --- API upload endpoint tests ---


def test_api_upload_requires_auth(client):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["test@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/api/v1/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 401


def test_api_upload_valid_csv(client, auth_headers):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["researcher@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
        ["researcher@example.com", "1002", "BACKGROUND.Medical History.Hypertension: Yes", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/api/v1/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        headers=auth_headers,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["data"]["summary"]["total"] == 2
    assert data["data"]["summary"]["created"] == 2


# --- Preview endpoint tests ---


def test_api_preview_returns_parsed_configs(client, auth_headers):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["alice@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
        ["alice@example.com", "1001", "BACKGROUND.Medical History.Hypertension: Yes", "FALSE", "TRUE", ""],
        ["bob@example.com", "1002", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/api/v1/config/upload/preview",
        data={"file": _make_csv_file(csv_rows)},
        headers=auth_headers,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["data"]["total"] == 2  # Two distinct (user, case) combos
    assert len(data["data"]["users"]) == 2
    assert len(data["data"]["cases"]) == 2


def test_admin_preview_no_auth_needed(client):
    """Admin preview doesn't require API key."""
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["test@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/admin/config/upload/preview",
        data={"file": _make_csv_file(csv_rows)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200


# --- CSV with experiment metadata columns ---


def test_upload_csv_with_experiment_metadata_columns(client, auth_headers):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top", "Experiment", "Arm", "Policy"],
        ["test@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", "", "eval_001", "learned", "thompson_v1"],
    ]
    response = client.post(
        "/api/v1/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        headers=auth_headers,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["data"]["summary"]["created"] == 1


def test_upload_multiple_users_and_cases(client, auth_headers):
    csv_rows = [
        ["User", "Case No.", "Path", "Collapse", "Highlight", "Top"],
        ["alice@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
        ["alice@example.com", "1001", "BACKGROUND.Medical History.Hypertension: Yes", "FALSE", "FALSE", ""],
        ["alice@example.com", "1002", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
        ["bob@example.com", "1001", "BACKGROUND.Family History.Cancer: No", "FALSE", "TRUE", ""],
    ]
    response = client.post(
        "/api/v1/config/upload",
        data={"file": _make_csv_file(csv_rows)},
        headers=auth_headers,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    # 3 distinct (user, case) combos: (alice, 1001), (alice, 1002), (bob, 1001)
    assert data["data"]["summary"]["total"] == 3
    assert data["data"]["summary"]["created"] == 3
