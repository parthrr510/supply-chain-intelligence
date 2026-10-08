import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from api_interface.api.main import app

client = TestClient(app)


@patch("api_interface.api.routers.dq.settings")
def test_get_dq_report_success(mock_settings, tmp_path):
    report_data = {"report_version": "1.0", "findings": []}
    temp_file = tmp_path / "dq_report.json"
    temp_file.write_text(json.dumps(report_data))

    mock_settings.dq_report_path = str(temp_file)

    response = client.get("/data-quality/report")
    assert response.status_code == 200
    assert response.json() == report_data


@patch("api_interface.api.routers.dq.settings")
def test_get_dq_report_unavailable(mock_settings, tmp_path):
    temp_file = tmp_path / "missing.json"
    mock_settings.dq_report_path = str(temp_file)

    response = client.get("/data-quality/report")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "DQ_REPORT_UNAVAILABLE"
