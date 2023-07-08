"""Email views."""
import asyncio
import traceback
from pathlib import Path
from typing import Optional

import jinja2
from cattrs import BaseValidationError, ClassValidationError
from loguru import logger
from quart import Response, request

from oes.webhooks.app import app
from oes.webhooks.email.sender import get_sender
from oes.webhooks.email.template import Attachments, Subject, render_message
from oes.webhooks.email.types import Email, EmailHookBody
from oes.webhooks.serialization import converter
from oes.webhooks.settings import Settings


@app.post("/email/<path:path>")
async def send_email(path: str) -> Response:
    """Send an email."""
    settings: Settings = app.config["settings"]

    if not settings.email.use:
        return Response(status=404)

    sender = get_sender(settings.email.use)

    body = await request.get_json()
    template_path = settings.email.template_path
    env = app.config["email_template_env"]

    try:
        _email = await asyncio.to_thread(
            _make_email, env, template_path, path, body, settings.email.email_from
        )
    except BaseValidationError:
        logger.error(f"Invalid email hook body:\n{traceback.format_exc()}")
        return Response(status=422)
    except jinja2.exceptions.TemplateNotFound:
        logger.error(f"The template {path!r} was not found.")
        return Response(status=404)

    await sender(_email, settings.email)

    logger.info(f"Sent message to {_email.to}")

    return Response(status=204)


def _make_email(
    env: jinja2.Environment,
    base_path: Path,
    path: str,
    body: dict,
    default_from: Optional[str],
) -> Email:
    try:
        hook = converter.structure(body, EmailHookBody)
    except Exception as e:
        raise ClassValidationError(str(e), (e,), EmailHookBody) from e

    subject = Subject(hook.subject)
    attachments = Attachments(base_path)

    text, html = render_message(env, subject, attachments, path, body)

    from_ = hook.from_ or default_from
    if not from_:
        exc = ValueError("Default 'email_from` is not set.")
        raise ClassValidationError(str(exc), (exc,), EmailHookBody)

    email = Email(
        to=hook.to,
        from_=from_,
        subject=str(subject) or None,
        text=text,
        html=html,
        attachments=tuple(attachments),
    )

    return email
