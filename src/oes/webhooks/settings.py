"""Settings module."""
from pathlib import Path
from typing import Optional

import typed_settings as ts
from attrs import define
from ruamel.yaml import YAML

from oes.webhooks.email.types import EmailSenderType
from oes.webhooks.serialization import converter


@define(kw_only=True)
class EmailSettings:
    """Email settings."""

    email_from: Optional[str] = None
    """The ``From`` value for email messages."""

    template_path: Path = Path("templates/email")
    """Path to the email template directory."""

    use: Optional[EmailSenderType] = None
    """The implementation to use."""


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
