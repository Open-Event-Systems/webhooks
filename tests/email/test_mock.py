import pytest

from oes.webhooks.email.mock import mock_email_sender
from oes.webhooks.email.types import Email


@pytest.mark.asyncio
async def test_mock():
    await mock_email_sender(
        Email(
            to="to@test.com",
            from_="from@test.com",
            subject="Test",
            text="Test",
        )
    )
