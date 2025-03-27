from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consumer import consume_shipment_updates, debounce_update, is_valid_shipment


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
        patch("consumer.consumer", mock_consumer),
        patch("consumer.ui.notify") as mock_notify,
        patch("consumer.debounce_update", new_callable=AsyncMock),
    ):
        await consume_shipment_updates()
        mock_notify.assert_called()


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
async def test_debounce_update():
    with patch("consumer.update_ui", new_callable=AsyncMock) as mock_update_ui:
        await debounce_update()
        mock_update_ui.assert_called_once()
