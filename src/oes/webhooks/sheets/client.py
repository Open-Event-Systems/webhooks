"""Sheets client."""
import threading
from collections.abc import Mapping, Sequence
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from loguru import logger

from oes.webhooks.settings import GoogleSheetsHook


class GoogleSheetsClient:
    """Google Sheets API client."""

    def __init__(self, account_info: Mapping[str, str]):
        creds = Credentials.from_service_account_info(account_info)
        self._service = build("sheets", "v4", credentials=creds)
        self._lock = threading.Lock()

    def append(self, hook: GoogleSheetsHook, data: Mapping[str, Any]):
        """Append a row to the sheet."""
        values = _render_values(hook, data)
        with self._lock:
            self._append(hook.sheet_id, hook.range, [values])

    def _append(self, sheet_id: str, range: str, values: Sequence[Sequence[Any]]):
        sheets = self._service.spreadsheets()
        values_obj = sheets.values()

        request = values_obj.append(
            spreadsheetId=sheet_id,
            range=range,
            valueInputOption="USER_ENTERED",
            body={
                "values": values,
            },
        )
        request.execute()
        logger.debug(f"Appended {values!r} row to {sheet_id}")


def _render_values(hook: GoogleSheetsHook, data: Mapping[str, Any]) -> Sequence[str]:
    columns = []
    for value_tmpl in hook.values:
        columns.append(str(value_tmpl(data)))
    return columns
