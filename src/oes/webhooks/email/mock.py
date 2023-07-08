"""Mock sender."""
import asyncio

from loguru import logger

from oes.webhooks.email.types import Email


async def mock_email_sender(email: Email):
    """Mock email sender."""
    msg = await asyncio.to_thread(email.get_message)
    msg_str = bytes(msg).decode()

    logger.info(f"Mock send:\n\n{msg_str}")
