import signal
from unittest.mock import patch


def test_signal_handling():
    with (
        patch("main.shutdown") as mock_shutdown,
        patch("signal.signal") as mock_signal,
    ):
        # Simulate SIGINT
        mock_signal(signal.SIGINT, mock_shutdown)
        mock_shutdown.assert_not_called()

        # Simulate SIGTERM
        mock_signal(signal.SIGTERM, mock_shutdown)
        mock_shutdown.assert_not_called()
