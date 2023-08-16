"""Sheets hook views."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from quart import Response, request
from werkzeug.exceptions import NotFound

from oes.webhooks.app import app
from oes.webhooks.settings import Settings

if TYPE_CHECKING:
    from oes.webhooks.sheets.client import GoogleSheetsClient


@app.post("/sheets/<string:hook_id>")
async def sheets_hook(hook_id: str) -> Response:
    """Append a row."""
    settings: Settings = app.config["settings"]
    sheets_client: Optional[GoogleSheetsClient] = app.config.get("sheets_client")
    if sheets_client is None:
        raise NotFound

    hook = next((h for h in settings.google.sheets_hooks if h.id == hook_id), None)
    if hook is None:
        raise NotFound

    data = await request.get_json()

    await asyncio.to_thread(sheets_client.append, hook, data)
    return Response(status=204)
