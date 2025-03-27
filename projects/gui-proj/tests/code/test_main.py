import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import (
    calculate_eta,
    consume_shipment_updates,
    debounce_update,
    filter_shipments,
    is_valid_shipment,
    set_status_filter,
    shutdown,
    update_shipment_list,
    update_shipment_map,
    update_ui,
)


@pytest.mark.parametrize(
    "shipment, expected_eta",
    [
        (
            {"latitude": "40.730610", "longitude": "-73.935242"},
            "0.0 hours",  # Close to NYC
        ),
        (
            {"latitude": "34.052235", "longitude": "-118.243683"},
            "40.8 hours",  # Los Angeles
        ),
        ({}, "Unknown ETA"),  # Missing data
    ],
)
def test_calculate_eta(shipment, expected_eta):
    assert calculate_eta(shipment) == expected_eta


@pytest.mark.parametrize(
    "event, expected_validity",
    [
        (
            {
                "shipment_id": "123",
                "status": "In Transit",
                "location": "NYC",
                "timestamp": "2023-01-01T12:00:00",
            },
            True,
        ),
        (
            {"shipment_id": "123", "status": "In Transit", "location": "NYC"},
            False,  # Missing timestamp
        ),
    ],
)
def test_is_valid_shipment(event, expected_validity):
    assert is_valid_shipment(event) == expected_validity


@pytest.mark.asyncio
async def test_set_status_filter():
    with (
        patch("main.update_shipment_list", new_callable=AsyncMock) as mock_update_list,
        patch("main.update_shipment_map", new_callable=AsyncMock) as mock_update_map,
    ):
        set_status_filter("Delivered")
        assert mock_update_list.called
        assert mock_update_map.called


@pytest.mark.asyncio
async def test_filter_shipments():
    with patch("main.ui") as mock_ui:
        filter_shipments("123")
        assert mock_ui.loading.called
        assert mock_ui.label.call_count == 2  # Header + one matching shipment


@pytest.mark.asyncio
async def test_consume_shipment_updates():
    mock_consumer = MagicMock()
    mock_consumer.__iter__.return_value = iter(
        [
            MagicMock(
                value={
                    "shipment_id": 1,
                    "status": "In Transit",
                    "location": "NY",
                    "timestamp": "2023-01-01",
                }
            ),
        ]
    )
    with (
        patch("main.consumer", mock_consumer),
        patch("main.ui.notify") as mock_notify,
        patch("main.debounce_update", new_callable=AsyncMock),
    ):
        await consume_shipment_updates()
        mock_notify.assert_called()


@pytest.mark.asyncio
async def test_debounce_update():
    with patch("main.update_ui", new_callable=AsyncMock) as mock_update_ui:
        await debounce_update()
        mock_update_ui.assert_called_once()


@pytest.mark.asyncio
async def test_update_ui():
    with (
        patch("main.update_shipment_list", new_callable=AsyncMock) as mock_update_list,
        patch("main.update_shipment_map", new_callable=AsyncMock) as mock_update_map,
    ):
        await update_ui()
        assert mock_update_list.called
        assert mock_update_map.called


@pytest.mark.asyncio
async def test_update_shipment_list():
    with patch("main.ui") as mock_ui:
        await update_shipment_list()
        assert mock_ui.loading.called
        assert mock_ui.label.called


@pytest.mark.asyncio
async def test_update_shipment_map():
    with patch("main.shipment_map") as mock_map:
        await update_shipment_map()
        assert mock_map.figure is not None


def test_shutdown():
    with (
        patch("main.consumer.close") as mock_close,
        patch("main.ui.notify") as mock_notify,
    ):
        shutdown()
        mock_close.assert_called_once()
        mock_notify.assert_called_once_with("Application shutting down...", type="info")


def test_signal_handlers():
    with patch("main.shutdown") as mock_shutdown:
        # Test SIGINT handler
        signal.getsignal(signal.SIGINT)(None, None)
        mock_shutdown.assert_called_once()

        # Test SIGTERM handler
        mock_shutdown.reset_mock()
        signal.getsignal(signal.SIGTERM)(None, None)
        mock_shutdown.assert_called_once()


def test_ui_initialization():
    with patch("main.ui") as mock_ui:
        # Test label creation
        mock_label = MagicMock()
        mock_ui.label.return_value = mock_label
        mock_label.classes.assert_called_with("text-2xl font-bold")

        # Test select creation
        mock_select = MagicMock()
        mock_ui.select.return_value = mock_select
        mock_select.on_change.assert_called()

        # Test button creation
        mock_button = MagicMock()
        mock_ui.button.return_value = mock_button
        mock_button.on_click.assert_called()
