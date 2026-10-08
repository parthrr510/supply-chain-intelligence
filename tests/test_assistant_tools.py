from unittest.mock import patch

from ai_agent.assistant.tools import get_route_stats, predict_delay, query_shipments


@patch("ai_agent.assistant.tools.get_shipments")
def test_query_shipments_success(mock_get_shipments):
    mock_get_shipments.return_value = ([{"id": "SHP-1"}], 1)

    result = query_shipments.invoke({"origin": "CNSHG", "page_size": 10})

    assert "error" not in result
    assert result["returned_count"] == 1
    assert result["total_matches"] == 1
    assert result["shipments"] == [{"id": "SHP-1"}]
    mock_get_shipments.assert_called_once_with(
        origin="CNSHG",
        destination=None,
        status=None,
        start_date=None,
        end_date=None,
        page=1,
        page_size=10,
    )


@patch("ai_agent.assistant.tools.get_shipments")
def test_query_shipments_bounds_size(mock_get_shipments):
    mock_get_shipments.return_value = ([], 0)

    result = query_shipments.invoke({"page_size": 100})

    assert "error" not in result
    mock_get_shipments.assert_called_once_with(
        origin=None,
        destination=None,
        status=None,
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
    )


def test_query_shipments_invalid_date():
    result = query_shipments.invoke({"start_date": "invalid-date"})
    assert "error" in result


@patch("ai_agent.assistant.tools._service_get_route_stats")
def test_get_route_stats_success(mock_get_route_stats):
    mock_get_route_stats.return_value = {
        "origin": "CNSHG",
        "destination": "USLAX",
        "shipment_count": 10,
        "average_delay_hours": 5.0,
        "on_time_rate": 0.8,
    }

    result = get_route_stats.invoke({"origin": "CNSHG", "destination": "USLAX", "date_range": "Q1"})

    assert "error" not in result
    assert result["shipment_count"] == 10
    mock_get_route_stats.assert_called_once_with(origin="CNSHG", destination="USLAX")


@patch("ai_agent.assistant.tools.prediction_service")
def test_predict_delay_success(mock_prediction_service):
    mock_prediction_service.predict_delay.return_value = {
        "probability": 0.8,
        "prediction": True,
        "threshold": 0.5,
        "model_version": "1.0",
    }

    result = predict_delay.invoke({"shipment_id": "SHP-1"})

    assert "error" not in result
    assert result["prediction"] is True
    mock_prediction_service.predict_delay.assert_called_once_with("SHP-1")


@patch("ai_agent.assistant.tools.prediction_service")
def test_predict_delay_error(mock_prediction_service):
    mock_prediction_service.predict_delay.side_effect = ValueError("Shipment not found")

    result = predict_delay.invoke({"shipment_id": "SHP-INVALID"})

    assert "error" in result
    assert "Shipment not found" in result["error"]
