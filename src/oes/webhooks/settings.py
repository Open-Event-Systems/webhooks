"""Settings module."""
import json
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Literal, NewType, Optional

import jinja2
import typed_settings as ts
from attrs import field
from jinja2 import ChainableUndefined
from jinja2.sandbox import ImmutableSandboxedEnvironment
from ruamel.yaml import YAML
from typed_settings import EnvLoader, FileLoader, SecretStr
from typed_settings.types import OptionList, SettingsClass, SettingsDict

_jinja2_env = ImmutableSandboxedEnvironment(
    undefined=ChainableUndefined,
)


class EmailSenderType(str, Enum):
    """An email sender type."""

    mock = "mock"
    smtp = "smtp"
    mailgun = "mailgun"


@ts.settings(kw_only=True)
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


@ts.settings(kw_only=True)
class MailgunSettings:
    """Mailgun settings."""

    base_url: str = "https://api.mailgun.net"
    """The base Mailgun URL."""

    domain: str = ""
    """The domain to send from."""

    api_key: SecretStr = ts.secret()
    """The API key."""


@ts.settings(kw_only=True)
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


@ts.settings(kw_only=True)
class GoogleSheetsHook:
    """A Google Sheets hook."""

    id: str = ""
    """The hook ID."""

    sheet_id: str = ""
    """The Sheet ID to append to."""

    range: str = "1:2"
    """The range to search for a table in."""

    values: Sequence[jinja2.environment.TemplateExpression] = ()
    """Column value template expressions."""


_ServiceAccountCredentials = NewType("_ServiceAccountCredentials", Mapping[str, str])


@ts.settings(kw_only=True)
class GoogleSettings:
    """Google settings."""

    service_account_credentials: _ServiceAccountCredentials = field(
        factory=lambda: _ServiceAccountCredentials(dict()),
    )
    """Service account credentials."""

    sheets_hooks: Sequence[GoogleSheetsHook] = ()
    """Google Sheets hooks."""


@ts.settings(kw_only=True)
class Settings:
    """Settings object."""

    email: EmailSettings = field(factory=EmailSettings)
    google: GoogleSettings = field(factory=GoogleSettings)


yaml = YAML(typ="safe")


def load_settings(config: Optional[Path]) -> Settings:
    """Load the settings."""
    loaders = []

    converter = ts.default_converter().copy()
    converter.register_structure_hook(
        _ServiceAccountCredentials, lambda v, t: _parse_service_account_credentials(v)
    )
    converter.register_structure_hook(
        jinja2.environment.TemplateExpression, lambda v, t: _compile_expression(v)
    )

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

    return ts.load_settings(Settings, loaders, converter=converter)


def _compile_expression(v):
    if isinstance(v, str):
        return _jinja2_env.compile_expression(v)
    else:
        return v


def _parse_service_account_credentials(v):
    if v and isinstance(v, str):
        return json.loads(v)
    else:
        return v or {}


def _yaml_format(
    path: Path, settings_cls: SettingsClass, options: OptionList
) -> SettingsDict:
    return yaml.load(path)
