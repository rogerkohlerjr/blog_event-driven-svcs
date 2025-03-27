import asyncio

# ...existing code...


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
            if is_valid_shipment(event):
                shipment_id = event["shipment_id"]
                shipments[shipment_id] = event
                ui.notify(
                    f"Shipment {shipment_id} updated: {event['status']} at {event['location']}"
                )
                await debounce_update()
            else:
                ui.notify(f"Invalid shipment data received: {event}", type="error")
    except Exception as e:
        ui.notify(f"Error consuming shipment updates: {e}", type="error")


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


update_task = None


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
    await asyncio.sleep(0.5)  # Wait for 500ms before updating
    await update_shipment_list()
    await update_shipment_map()
