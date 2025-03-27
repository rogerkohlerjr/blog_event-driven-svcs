from unittest.mock import MagicMock, patch

import pytest

from ui import calculate_eta, update_shipment_list


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


@pytest.mark.asyncio
async def test_update_shipment_list():
    mock_ui = MagicMock()
    mock_ui.loading = MagicMock()
    mock_ui.label = MagicMock()
    mock_shipment_table = MagicMock()
    mock_shipments = {
        1: {
            "shipment_id": 1,
            "status": "in_transit",
            "location": "NY",
            "timestamp": "2023-01-01",
        },
        2: {
            "shipment_id": 2,
            "status": "delivered",
            "location": "CA",
            "timestamp": "2023-01-02",
        },
    }

    with (
        patch("ui.ui", mock_ui),
        patch("ui.shipment_table", mock_shipment_table),
        patch("ui.shipments", mock_shipments),
        patch("ui.selected_status", "All"),
        patch("ui.calculate_eta", return_value="5.0 hours"),
    ):
        await update_shipment_list()

    mock_shipment_table.clear.assert_called_once()
    assert mock_ui.label.call_count == len(mock_shipments) + 1  # +1 for the header


def test_ui_elements():
    with patch("ui.ui") as mock_ui:
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
