from geopy.distance import geodesic

# ...existing code...


async def update_shipment_list():
    """
    Refresh the shipment list in the UI based on the selected status.

    The function clears the current shipment table and repopulates it
    with shipments matching the selected status filter.
    """
    with ui.loading():
        shipment_table.clear()
        with shipment_table:
            ui.label("Shipment ID | Status | Location | Timestamp | ETA").style(
                "font-weight: bold;"
            )
            for shipment in shipments.values():
                if selected_status == "All" or shipment["status"] == selected_status:
                    eta = calculate_eta(shipment)
                    ui.label(
                        f"{shipment['shipment_id']} | {shipment['status']} | {shipment['location']} | {shipment['timestamp']} | {eta}"
                    )


def calculate_eta(shipment):
    """
    Calculate the estimated time of arrival (ETA) for a shipment.

    Parameters
    ----------
    shipment : dict
        A dictionary containing shipment details, including latitude
        and longitude.

    Returns
    -------
    str
        The estimated time of arrival in hours, or "Unknown ETA" if
        required data is missing.
    """
    try:
        current_location = (float(shipment["latitude"]), float(shipment["longitude"]))
        destination = (40.7128, -74.0060)  # Example: New York City coordinates
        distance = geodesic(current_location, destination).kilometers
        average_speed = 60  # Assume 60 km/h
        eta_hours = distance / average_speed
        return f"{eta_hours:.1f} hours"
    except KeyError:
        return "Unknown ETA"


ui.button("Refresh", on_click=lambda: asyncio.create_task(update_ui()))
ui.input("Search by Shipment ID", on_change=lambda e: filter_shipments(e.value))
