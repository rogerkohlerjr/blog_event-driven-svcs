from constants import STATUS_OPTIONS


def test_status_options():
    assert isinstance(STATUS_OPTIONS, list)
    assert STATUS_OPTIONS == ["All", "In Transit", "Out for Delivery", "Delivered"]
