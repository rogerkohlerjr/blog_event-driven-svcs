import asyncio
import json
import logging
import signal
from asyncio import sleep

import plotly.graph_objects as go
from geopy.distance import geodesic
from kafka import KafkaConsumer
from nicegui import ui

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka consumer to listen for shipment updates
consumer = KafkaConsumer(
    "shipment_updates",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

shipments = {}
selected_status = "All"
update_task = None


async def consume_shipment_updates():
    """
    Continuously consume shipment updates and update the UI.

    This function listens for shipment updates from a Kafka consumer,
    validates the data, and updates the UI accordingly.

    Raises
    ------
    Exception
        If an error occurs while consuming shipment updates.
    """
    try:
        for message in consumer:
            event = message.value
            shipment_id = event["shipment_id"]
            if is_valid_shipment(event):
                shipments[shipment_id] = event
                ui.notify(
                    f"Shipment {shipment_id} updated: {event['status']} at {event['location']}"
                )
                logger.info("Shipment update received: %s", event)
                await (
                    debounce_update()
                )  # Await debounce_update to ensure proper execution
            else:
                ui.notify(f"Invalid shipment data received: {event}", type="error")
    except Exception as e:
        ui.notify(f"Error consuming shipment updates: {e}", type="error")


async def debounce_update():
    """
    Debounce UI updates to avoid frequent refreshes.

    Cancels any ongoing update task and schedules a new one after a
    short delay.
    """
    global update_task
    if update_task:
        update_task.cancel()
    update_task = asyncio.create_task(update_ui())


async def update_ui():
    """
    Update the UI components, including the shipment list and map.

    This function waits for a short delay before refreshing the UI to
    reduce the frequency of updates.
    """
    await sleep(0.5)  # Wait for 500ms before updating
    await update_shipment_list()
    await update_shipment_map()


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


async def update_shipment_map():
    """
    Update the map with current shipment locations based on the selected status.

    Filters shipments by the selected status and updates the map with
    their locations.
    """
    filtered_shipments = [
        s
        for s in shipments.values()
        if selected_status == "All" or s["status"] == selected_status
    ]
    locations = [
        go.Scattergeo(
            lon=[float(s["longitude"]) for s in filtered_shipments if "longitude" in s],
            lat=[float(s["latitude"]) for s in filtered_shipments if "latitude" in s],
            text=[s["shipment_id"] for s in filtered_shipments],
            mode="markers",
            marker=dict(size=10, color="blue"),
        )
    ]
    shipment_map.figure = go.Figure(
        data=locations, layout=go.Layout(title="Real-Time Shipment Locations")
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


def set_status_filter(status):
    """
    Update the selected status filter and refresh the UI.

    Parameters
    ----------
    status : str
        The status to filter shipments by.
    """
    global selected_status
    selected_status = status
    asyncio.create_task(
        update_shipment_list()
    )  # Retain asyncio.create_task for background updates
    asyncio.create_task(update_shipment_map())


def is_valid_shipment(event):
    """
    Validate the shipment event data.

    Parameters
    ----------
    event : dict
        The shipment event data to validate.

    Returns
    -------
    bool
        True if the event contains all required fields, False otherwise.
    """
    required_fields = {"shipment_id", "status", "location", "timestamp"}
    return required_fields.issubset(event.keys())


def filter_shipments(shipment_id):
    """
    Filter shipments by the given shipment ID and update the UI.

    Parameters
    ----------
    shipment_id : str
        The shipment ID to filter by.
    """
    filtered_shipments = {k: v for k, v in shipments.items() if shipment_id in k}
    with ui.loading():
        shipment_table.clear()
        with shipment_table:
            ui.label("Shipment ID | Status | Location | Timestamp | ETA").style(
                "font-weight: bold;"
            )
            for shipment in filtered_shipments.values():
                eta = calculate_eta(shipment)
                ui.label(
                    f"{shipment['shipment_id']} | {shipment['status']} | {shipment['location']} | {shipment['timestamp']} | {eta}"
                )


def shutdown():
    """
    Shut down the application gracefully.

    Closes the Kafka consumer and notifies the user of the shutdown.
    """
    consumer.close()
    ui.notify("Application shutting down...", type="info")


signal.signal(signal.SIGINT, lambda *_: shutdown())
signal.signal(signal.SIGTERM, lambda *_: shutdown())

# UI layout
ui.label("📦 Real-Time Shipment Tracking").classes("text-2xl font-bold")
ui.label("Filter by Status:")

STATUS_OPTIONS = ["All", "In Transit", "Out for Delivery", "Delivered"]

status_filter = ui.select(
    STATUS_OPTIONS,
    value="All",
    on_change=lambda e: set_status_filter(e.value),
)

ui.button("Refresh", on_click=lambda: asyncio.create_task(update_ui()))
ui.input("Search by Shipment ID", on_change=lambda e: filter_shipments(e.value))
shipment_table = ui.column()
figure = go.Figure(data=[], layout=go.Layout(title="Real-Time Shipment Locations"))
shipment_map = ui.plotly(figure)

# Start consuming shipment updates in the background
asyncio.create_task(consume_shipment_updates())

logger.info("Application started.")

ui.run(title="Shipment Tracking Dashboard")
