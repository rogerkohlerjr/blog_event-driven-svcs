from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import consume_shipment_updates, shutdown, update_ui


@pytest.mark.asyncio
async def test_integration_consume_and_update_ui():
    """
    Test the integration between consuming shipment updates and updating the UI.
    """
    mock_consumer = MagicMock()
    mock_consumer.__iter__.return_value = iter(
        [
            MagicMock(
                value={
                    "shipment_id": 1,
                    "status": "In Transit",
                    "location": "NY",
                    "timestamp": "2023-01-01",
                    "latitude": "40.730610",
                    "longitude": "-73.935242",
                }
            ),
            MagicMock(
                value={
                    "shipment_id": 2,
                    "status": "Delivered",
                    "location": "CA",
                    "timestamp": "2023-01-02",
                    "latitude": "34.052235",
                    "longitude": "-118.243683",
                }
            ),
        ]
    )

    mock_ui = MagicMock()
    mock_shipments = {}

    with (
        patch("main.consumer", mock_consumer),
        patch("main.ui", mock_ui),
        patch("main.shipments", mock_shipments),
        patch("main.update_ui", new_callable=AsyncMock),
    ):
        await consume_shipment_updates()
        assert len(mock_shipments) == 2
        assert mock_ui.notify.call_count == 2
        mock_ui.notify.assert_any_call(
            "Shipment 1 updated: In Transit at NY", type="info"
        )
        mock_ui.notify.assert_any_call(
            "Shipment 2 updated: Delivered at CA", type="info"
        )


@pytest.mark.asyncio
async def test_integration_ui_refresh():
    """
    Test the integration of UI refresh logic with mocked data.
    """
    mock_ui = MagicMock()
    mock_shipments = {
        1: {
            "shipment_id": 1,
            "status": "In Transit",
            "location": "NY",
            "timestamp": "2023-01-01",
            "latitude": "40.730610",
            "longitude": "-73.935242",
        },
        2: {
            "shipment_id": 2,
            "status": "Delivered",
            "location": "CA",
            "timestamp": "2023-01-02",
            "latitude": "34.052235",
            "longitude": "-118.243683",
        },
    }

    with (
        patch("main.ui", mock_ui),
        patch("main.shipments", mock_shipments),
        patch("main.selected_status", "All"),
    ):
        await update_ui()
        assert mock_ui.loading.called
        assert mock_ui.label.call_count == len(mock_shipments) + 1  # Header + shipments


def test_integration_shutdown():
    """
    Test the integration of the shutdown process.
    """
    mock_consumer = MagicMock()
    mock_ui = MagicMock()

    with (
        patch("main.consumer", mock_consumer),
        patch("main.ui", mock_ui),
    ):
        shutdown()
        mock_consumer.close.assert_called_once()
        mock_ui.notify.assert_called_once_with(
            "Application shutting down...", type="info"
        )


@pytest.mark.asyncio
async def test_ui_full_lifecycle():
    """
    Test the full lifecycle of all UI elements: initialization, updates, and shutdown.
    """
    mock_ui = MagicMock()
    mock_consumer = MagicMock()
    mock_consumer.__iter__.return_value = iter(
        [
            MagicMock(
                value={
                    "shipment_id": 1,
                    "status": "In Transit",
                    "location": "NY",
                    "timestamp": "2023-01-01",
                    "latitude": "40.730610",
                    "longitude": "-73.935242",
                }
            ),
            MagicMock(
                value={
                    "shipment_id": 2,
                    "status": "Delivered",
                    "location": "CA",
                    "timestamp": "2023-01-02",
                    "latitude": "34.052235",
                    "longitude": "-118.243683",
                }
            ),
        ]
    )
    mock_shipments = {}
    mock_selected_status = "All"

    with (
        patch("main.ui", mock_ui),
        patch("main.consumer", mock_consumer),
        patch("main.shipments", mock_shipments),
        patch("main.selected_status", mock_selected_status),
        patch("main.update_ui", new_callable=AsyncMock),
    ):
        # Test UI initialization
        await update_ui()
        assert mock_ui.loading.called
        assert mock_ui.label.call_count == len(mock_shipments) + 1  # Header + shipments

        # Test UI updates
        await consume_shipment_updates()
        assert len(mock_shipments) == 2
        assert mock_ui.notify.call_count == 2
        mock_ui.notify.assert_any_call(
            "Shipment 1 updated: In Transit at NY", type="info"
        )
        mock_ui.notify.assert_any_call(
            "Shipment 2 updated: Delivered at CA", type="info"
        )

        # Test UI shutdown
        shutdown()
        mock_consumer.close.assert_called_once()
        mock_ui.notify.assert_called_with("Application shutting down...", type="info")
