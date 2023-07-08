"""Settings module."""
from enum import Enum
from pathlib import Path
from typing import Optional

import typed_settings as ts
from attrs import define
from ruamel.yaml import YAML
from typed_settings import SecretStr

from oes.webhooks.serialization import converter


class EmailSenderType(str, Enum):
    """An email sender type."""

    mock = "mock"
    mailgun = "mailgun"


@define(kw_only=True)
class MailgunSettings:
    """Mailgun settings."""

    base_url: str = "https://api.mailgun.net"
    """The base Mailgun URL."""

    domain: str
    """The domain to send from."""

    api_key: SecretStr = ts.secret()
    """The API key."""


@define(kw_only=True)
class EmailSettings:
    """Email settings."""

    email_from: Optional[str] = None
    """The ``From`` value for email messages."""

    template_path: Path = Path("templates/email")
    """Path to the email template directory."""

    use: Optional[EmailSenderType] = None
    """The implementation to use."""

    mailgun: Optional[MailgunSettings] = None
    """Mailgun settings."""


@define(kw_only=True)
class Settings:
    """Settings object."""

    email: EmailSettings = EmailSettings()


yaml = YAML(typ="safe")


def load_settings(config: Optional[Path]) -> Settings:
    """Load the settings."""
    loaders = []

    if config:
        with config.open() as f:
            doc = yaml.load(f)
        inst = converter.structure(doc, Settings)
        loaders.append(ts.loaders.InstanceLoader(inst))

    loaders.append(ts.loaders.EnvLoader("OES_WEBHOOKS"))

    return ts.load_settings(
        Settings,
        loaders,
    )
