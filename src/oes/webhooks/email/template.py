"""Template module."""
import itertools
import mimetypes
from collections.abc import Iterator
from pathlib import Path
from typing import Optional, Union

import jinja2.sandbox
from jinja2 import ChainableUndefined

from oes.webhooks.email.html import process_html
from oes.webhooks.email.types import Attachment, AttachmentType


class Attachments:
    """Class that allows templates to include attachments."""

    _base_path: Path
    _attachments: dict[str, Attachment]

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self._attachments = {}
        self._ids = itertools.count(1)

    def __iter__(self) -> Iterator[Attachment]:
        return iter(self._attachments.values())

    def add(
        self,
        path: Union[str, Path],
        name: Optional[str] = None,
        media_type: Optional[str] = None,
        inline: bool = False,
    ) -> str:
        """Include the file as an attachment.

        Args:
            path: The path, relative to the base template directory.
            name: The filename.
            media_type: The MIME type.
            inline: Whether the attachment is inline.

        Returns:
            The Content-ID value.
        """
        path_obj = self._base_path / Path(path)
        if not path_obj.is_relative_to(self._base_path):
            raise ValueError(f"Path is not within the template directory: {path}")

        id_ = f"attachment{next(self._ids)}"
        with path_obj.open("rb") as f:
            data = f.read()

        filename = name if name is not None else path_obj.parts[-1]

        if media_type is None:
            type_, _ = mimetypes.guess_type(path_obj)
            media_type = type_ or "application/octet-stream"

        self._attachments[id_] = Attachment(
            id=id_,
            name=filename,
            data=data,
            media_type=media_type,
            attachment_type=AttachmentType.inline
            if inline
            else AttachmentType.attachment,
        )

        return id_

    def attach(
        self,
        path: Union[str, Path],
        name: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> str:
        """Include the file as an attachment.

        Args:
            path: The path, relative to the base template directory.
            name: The filename.
            media_type: The media type.

        Returns:
            The Content-ID value.
        """
        return self.add(path, name, media_type)

    def inline(
        self,
        path: Union[str, Path],
        name: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> str:
        """Include the file as an inline attachment.

        Args:
            path: The path, relative to the base template directory.
            name: The filename.
            media_type: The media type.

        Returns:
            The Content-ID value.
        """
        return self.add(path, name, media_type, inline=True)


class Subject:
    """Class that allows templates to set the subject."""

    default_subject: Optional[str]
    subject: Optional[str]

    def __init__(self, default_subject: Optional[str]):
        self.default_subject = default_subject
        self.subject = default_subject

    def set_subject(self, subject: str) -> str:
        """Set and return the subject."""
        self.subject = subject
        return subject

    def set_subject_or_default(self, subject: str) -> str:
        """Set the subject if there is no default."""
        if self.subject:
            return self.subject
        elif self.default_subject:
            return self.default_subject
        else:
            self.subject = subject
            return subject

    def __str__(self) -> str:
        return self.subject or self.default_subject or ""

    def __bool__(self) -> bool:
        return bool(str(self))


def get_environment(base_path: Path) -> jinja2.Environment:
    """Configure a Jinja2 environment.

    Args:
        base_path: The base template directory.
    """
    loader = jinja2.FileSystemLoader(base_path)
    environment = jinja2.sandbox.ImmutableSandboxedEnvironment(
        loader=loader,
        undefined=ChainableUndefined,
    )
    return environment


def render_message(
    env: jinja2.Environment,
    subject: Subject,
    attachments: Attachments,
    template_name: str,
    data: dict,
) -> tuple[str, Optional[str]]:
    """Render the text and HTML messages for an email.

    Args:
        env: The Jinja2 environment.
        subject: A :class:`Subject` instance.
        attachments: An :class:`Attachments` instance.
        template_name: The template name, without an extension.
        data: The data to render the template with.

    Returns:
        A pair of the text and HTML result.
    """
    text = render_template(
        env,
        subject,
        attachments,
        f"{template_name}.txt",
        data,
    )

    try:
        html = render_template(
            env,
            subject,
            attachments,
            f"{template_name}.html",
            data,
        )
        html = process_html(html)
    except jinja2.exceptions.TemplateNotFound:
        html = None

    return text, html


def render_template(
    env: jinja2.Environment,
    subject: Subject,
    attachments: Attachments,
    template_name: str,
    data: dict,
) -> str:
    """Load and render the given template."""
    tmpl = env.get_template(
        template_name,
        globals={
            "set_subject": subject.set_subject,
            "default_subject": subject.set_subject_or_default,
            "attach": attachments.attach,
            "inline": attachments.inline,
        },
    )

    result = tmpl.render(
        {
            **data,
            "subject": subject,
        }
    )

    return result
