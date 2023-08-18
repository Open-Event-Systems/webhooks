"""Receipt veiws."""
from typing import Optional

import httpx
from quart import Response, request

from oes.webhooks.app import app

_client = httpx.AsyncClient(app=app)


@app.post("/receipt")
async def send_receipt():
    """Send a receipt email."""
    body = await request.get_json()

    email = _get_email(body["cart_data"])
    total = _get_total_without_modifiers(body["cart_data"])
    if email and total != 0:
        # kind of hacky to re-use a view
        res = await _client.post(
            f"{request.root_url}email/receipt",
            json={
                "to": email,
                "subject": "Order Confirmation",
                "checkout": body,
            },
        )
        res.raise_for_status()
    return Response(status=204)


def _get_email(cart_data: dict) -> Optional[str]:
    meta_email = cart_data.get("meta", {}).get("email")
    if meta_email:
        return meta_email

    for reg in cart_data["registrations"]:
        email = reg["new_data"].get("email")
        if email:
            return email

    return None


def _get_total_without_modifiers(cart_data: dict) -> int:
    total = 0
    for reg in cart_data["registrations"]:
        for line_item in reg["line_items"]:
            total += line_item["price"]
    return total
