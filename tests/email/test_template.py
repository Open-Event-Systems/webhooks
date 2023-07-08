from pathlib import Path

from oes.webhooks.email.template import Attachments, get_loader, render_template
from oes.webhooks.email.types import Attachment, AttachmentType


def test_template():
    attachments = Attachments(Path("tests/email/templates"))

    loader = get_loader(Path("tests/email/templates"))

    res = render_template(
        loader, attachments, "template.txt", {"subject": "Test", "text": "Test text."}
    )

    assert res == "Test\n\nTest text."


def test_template_attachments():
    attachments = Attachments(Path("tests/email/templates"))

    loader = get_loader(Path("tests/email/templates"))

    res = render_template(loader, attachments, "attachment.txt", {})

    assert res == "Attachment: attachment1"
    attached_objs = list(attachments)
    assert len(attached_objs) == 1
    assert attached_objs[0] == Attachment(
        id="attachment1",
        name="attachment.txt",
        data=b'Attachment: {{ attach("attachment.txt", attachment=true) }}',
        media_type="text/plain",
        attachment_type=AttachmentType.attachment,
    )
