"""Email webhook types."""
from collections.abc import Iterable, Sequence
from email.message import EmailMessage, MIMEPart
from enum import Enum
from typing import BinaryIO, Optional, Union

from attrs import frozen
from typing_extensions import TypeAlias

AttachmentData: TypeAlias = Union[bytes, bytearray, memoryview, BinaryIO]


class AttachmentType(str, Enum):
    """Attachment types."""

    inline = "inline"
    attachment = "attachment"


@frozen(kw_only=True)
class Attachment:
    """Attachment information."""

    id: str
    """The attachment ID."""

    name: Optional[str] = None
    """The attachment filename."""

    data: AttachmentData
    """The attachment data."""

    media_type: str
    """The media type."""

    attachment_type: AttachmentType = AttachmentType.attachment
    """The attachment type."""

    def make_attachment(self) -> MIMEPart:
        """Return a :class:`MIMEPart` for this attachment."""
        part = MIMEPart()

        if hasattr(self.data, "read"):
            content = self.data.read()
        else:
            content = bytes(self.data)

        main_type, _, subtype = self.media_type.partition("/")

        part.set_content(
            content,
            maintype=main_type,
            subtype=subtype,
            disposition=self.attachment_type,
            # the @ is "required" but works without it
            cid=f"<{self.id}>",
            filename=self.name,
        )

        return part


@frozen(kw_only=True)
class Email:
    """An email."""

    to: str
    """The ``To:`` address"""

    from_: str
    """The ``From:`` address."""

    subject: Optional[str] = None
    """The subject."""

    text: str
    """The plain message text."""

    html: Optional[str] = None
    """The HTML message text."""

    attachments: Sequence[Attachment] = ()
    """A mapping of attachment IDs to attachment data."""

    def get_message(self) -> EmailMessage:
        """Get a :class:`EmailMessage` object."""
        msg = EmailMessage()
        msg.make_mixed()

        if self.html:
            # HTML with fallback
            alt_part = MIMEPart()
            alt_part.make_alternative()
            alt_part.attach(_make_text_part(self.text))
            alt_part.attach(
                _make_html_part(
                    self.html,
                    (
                        att
                        for att in self.attachments
                        if att.attachment_type == AttachmentType.inline
                    ),
                )
            )
            msg.attach(alt_part)
        else:
            # Text only
            text_part = _make_text_part(self.text)
            msg.attach(text_part)

        # attachments
        for att in self.attachments:
            if att.attachment_type == AttachmentType.attachment:
                msg.attach(att.make_attachment())

        return msg


@frozen(kw_only=True)
class EmailHookBody:
    """The body of an email hook."""

    to: str
    from_: Optional[str] = None
    subject: Optional[str] = None


def _make_text_part(text: str) -> MIMEPart:
    part = MIMEPart()
    part.set_content(text)
    return part


def _make_html_part(html: str, inline_attachments: Iterable[Attachment]) -> MIMEPart:
    part = MIMEPart()
    part.make_related()

    part.add_related(html, subtype="html")

    for att in inline_attachments:
        part.attach(att.make_attachment())

    return part
