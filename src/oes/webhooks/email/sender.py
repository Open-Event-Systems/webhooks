"""Sender module."""
import asyncio
from collections.abc import Awaitable, Callable

import httpx
from httpx import BasicAuth
from loguru import logger
from typing_extensions import TypeAlias

from oes.webhooks.email.types import Email
from oes.webhooks.settings import EmailSenderType, EmailSettings

EmailSender: TypeAlias = Callable[[Email, EmailSettings], Awaitable]
"""A callable to send an email."""


def get_sender(typ: EmailSenderType) -> EmailSender:
    """Get a :class:`EmailSender`."""
    if typ == EmailSenderType.mock:
        return mock_email_sender
    elif typ == EmailSenderType.mailgun:
        return mailgun_email_sender
    else:
        raise ValueError(f"Invalid email sender type: {typ}")


_client = httpx.AsyncClient()


async def mock_email_sender(email: Email, settings: EmailSettings):
    """Mock email sender."""
    msg = await asyncio.to_thread(email.get_message)
    msg_str = bytes(msg).decode()

    logger.info(f"Mock send:\n\n{msg_str}")


async def mailgun_email_sender(email: Email, settings: EmailSettings):
    """Mailgun API."""
    mg_cfg = settings.mailgun
    if not mg_cfg:
        raise ValueError("Mailgun is not configured")

    url = f"{mg_cfg.base_url}/v3/{mg_cfg.domain}/messages.mime"
    user = "api"
    secret = mg_cfg.api_key

    msg = await asyncio.to_thread(email.get_message)

    msg.add_header("To", email.to)
    msg.add_header("From", email.from_)

    if email.subject:
        msg.add_header("Subject", email.subject)

    params = {
        "to": email.to,
    }

    files = {
        "message": bytes(msg),
    }

    res = await _client.post(
        url,
        auth=BasicAuth(user, secret),
        data=params,
        files=files,
    )
    if res.is_error:
        logger.error(f"Mailgun API request returned {res.status_code}: {res.text}")

    res.raise_for_status()
