"""Sender module."""

from oes.webhooks.email.mock import mock_email_sender
from oes.webhooks.email.types import EmailSender, EmailSenderType


def get_sender(typ: EmailSenderType) -> EmailSender:
    """Get a :class:`EmailSender`."""
    if typ == EmailSenderType.mock:
        return mock_email_sender
    else:
        raise ValueError(f"Invalid email sender type: {typ}")
