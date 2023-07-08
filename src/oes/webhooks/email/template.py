"""Template module."""
import itertools
import mimetypes
from collections.abc import Iterator
from pathlib import Path
from typing import Optional, Union

import jinja2.sandbox

from oes.webhooks.email.html import process_html
from oes.webhooks.email.types import Attachment, AttachmentType

jinja_env = jinja2.sandbox.ImmutableSandboxedEnvironment()


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

    def __call__(
        self,
        path: Union[str, Path],
        attachment: bool = False,
        name: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> str:
        path_obj = self._base_path / Path(path)
        if not path_obj.is_relative_to(self._base_path):
            raise ValueError(f"Path is not relative to the base path: {path}")

        id_ = f"attachment{next(self._ids)}"
        with path_obj.open("rb") as f:
            data = f.read()

        filename = name if name is not None else path_obj.parts[-1]

        if media_type is None:
            type_, _ = mimetypes.guess_type(path_obj)
            media_type = type_ or "application/octet-stream"

        self._attachments[id_] = Attachment(
            # the @ is "required" but works without it
            id=f"<{id_}>",
            name=filename,
            data=data,
            media_type=media_type,
            attachment_type=AttachmentType.attachment
            if attachment
            else AttachmentType.inline,
        )

        return id_


def get_loader(base_path: Path) -> jinja2.BaseLoader:
    """Get a template loader."""
    loader = jinja2.FileSystemLoader(base_path)
    return loader


def render_message(
    loader: jinja2.BaseLoader, attachments: Attachments, template_name: str, data: dict
) -> tuple[str, Optional[str]]:
    """Render the text and HTML messages for an email.

    Args:
        loader: The template loader.
        attachments: An :class:`Attachments` instance.
        template_name: The template name, without an extension.
        data: The data to render the template with.

    Returns:
        A pair of the text and HTML result.
    """
    text = render_template(
        loader,
        attachments,
        f"{template_name}.txt",
        data,
    )

    try:
        html = render_template(
            loader,
            attachments,
            f"{template_name}.html",
            data,
        )
        html = process_html(html)
    except jinja2.exceptions.TemplateNotFound:
        html = None

    return text, html


def render_template(
    loader: jinja2.BaseLoader,
    attachments: Attachments,
    template_name: str,
    data: dict,
) -> str:
    """Load and render the given template."""
    tmpl = loader.load(
        jinja_env,
        template_name,
        {
            "attach": attachments,
        },
    )
    result = tmpl.render(data)
    return result
