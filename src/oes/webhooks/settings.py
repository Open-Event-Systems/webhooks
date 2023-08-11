"""Settings module."""
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

import typed_settings as ts
from attrs import define, field
from ruamel.yaml import YAML
from typed_settings import EnvLoader, FileLoader, SecretStr
from typed_settings.types import OptionList, SettingsClass, SettingsDict


class EmailSenderType(str, Enum):
    """An email sender type."""

    mock = "mock"
    smtp = "smtp"
    mailgun = "mailgun"


@define(kw_only=True)
class SMTPSettings:
    """SMTP settings."""

    server: str = "localhost"
    """The SMTP server."""

    port: int = 587
    """The SMTP port."""

    tls: Optional[Literal["ssl", "starttls"]] = "starttls"
    """The SSL/TLS method."""

    username: str = ""
    """The SMTP username."""

    password: SecretStr = ts.secret(default="")
    """The SMTP password."""


@define(kw_only=True)
class MailgunSettings:
    """Mailgun settings."""

    base_url: str = "https://api.mailgun.net"
    """The base Mailgun URL."""

    domain: str = ""
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

    smtp: Optional[SMTPSettings] = None
    """SMTP settings."""

    mailgun: Optional[MailgunSettings] = None
    """Mailgun settings."""


@define(kw_only=True)
class Settings:
    """Settings object."""

    email: EmailSettings = field(factory=EmailSettings)


yaml = YAML(typ="safe")


def load_settings(config: Optional[Path]) -> Settings:
    """Load the settings."""
    loaders = []

    if config is not None:
        loaders.append(
            FileLoader(
                {
                    "*.yml": _yaml_format,
                    "*.yaml": _yaml_format,
                },
                (config,),
            )
        )

    loaders.append(EnvLoader("OES_WEBHOOKS_"))

    return ts.load_settings(Settings, loaders)


def _yaml_format(
    path: Path, settings_cls: SettingsClass, options: OptionList
) -> SettingsDict:
    return yaml.load(path)
