"""Sender module."""
import asyncio
import smtplib
from asyncio import Semaphore
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime

import httpx
from httpx import BasicAuth
from loguru import logger
from typing_extensions import TypeAlias

from oes.webhooks.email.types import Email
from oes.webhooks.settings import EmailSenderType, EmailSettings, SMTPSettings

EmailSender: TypeAlias = Callable[[Email, EmailSettings], Awaitable]
"""A callable to send an email."""


def get_sender(typ: EmailSenderType) -> EmailSender:
    """Get a :class:`EmailSender`."""
    if typ == EmailSenderType.mock:
        return mock_email_sender
    elif typ == EmailSenderType.smtp:
        return smtp_email_sender
    elif typ == EmailSenderType.mailgun:
        return mailgun_email_sender
    else:
        raise ValueError(f"Invalid email sender type: {typ}")


_client = httpx.AsyncClient()
_semaphore = Semaphore(1)


async def mock_email_sender(email: Email, settings: EmailSettings):
    """Mock email sender."""
    msg = await asyncio.to_thread(email.get_message)
    _set_date(msg)
    msg_str = bytes(msg).decode()

    logger.info(f"Mock send:\n\n{msg_str}")


async def smtp_email_sender(email: Email, settings: EmailSettings):
    """SMTP email sender."""
    smtp_settings = settings.smtp
    if not smtp_settings:
        raise ValueError("SMTP is not configured")

    async with _semaphore:
        await asyncio.to_thread(_smtp_email_sender, email, smtp_settings)


def _smtp_email_sender(email: Email, settings: SMTPSettings):
    smtp: smtplib.SMTP
    if settings.tls == "ssl":
        smtp = smtplib.SMTP_SSL(settings.server, settings.port)
    else:
        smtp = smtplib.SMTP(settings.server, settings.port)

    with smtp:
        if settings.tls == "starttls":
            smtp.starttls()

        smtp.login(settings.username, settings.password)

        msg = email.get_message()
        _set_date(msg)
        smtp.send_message(msg, from_addr=email.from_, to_addrs=(email.to,))


async def mailgun_email_sender(email: Email, settings: EmailSettings):
    """Mailgun API."""
    mg_cfg = settings.mailgun
    if not mg_cfg:
        raise ValueError("Mailgun is not configured")

    url = f"{mg_cfg.base_url}/v3/{mg_cfg.domain}/messages.mime"
    user = "api"
    secret = mg_cfg.api_key

    msg = await asyncio.to_thread(email.get_message)
    _set_date(msg)

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


def _set_date(msg: EmailMessage):
    now = datetime.now(tz=timezone.utc).astimezone()
    msg.add_header("Date", format_datetime(now))
