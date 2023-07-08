from pathlib import Path

from oes.webhooks.email.template import (
    Attachments,
    Subject,
    get_environment,
    render_template,
)
from oes.webhooks.email.types import Attachment, AttachmentType


def test_template():
    subject = Subject("Test")
    attachments = Attachments(Path("tests/email/templates"))

    env = get_environment(Path("tests/email/templates"))

    res = render_template(
        env, subject, attachments, "template.txt", {"text": "Test text."}
    )

    assert res == "Test\n\nTest text."


def test_template_attachments():
    subject = Subject(None)
    attachments = Attachments(Path("tests/email/templates"))

    env = get_environment(Path("tests/email/templates"))

    res = render_template(env, subject, attachments, "attachment.txt", {})

    assert res == "Attachment: attachment1"
    attached_objs = list(attachments)
    assert len(attached_objs) == 1
    assert attached_objs[0] == Attachment(
        id="attachment1",
        name="attachment.txt",
        data=b'Attachment: {{ attach("attachment.txt") }}\n',
        media_type="text/plain",
        attachment_type=AttachmentType.attachment,
    )


def test_template_attachments_inline():
    subject = Subject(None)
    attachments = Attachments(Path("tests/email/templates"))

    env = get_environment(Path("tests/email/templates"))

    res = render_template(env, subject, attachments, "inline.txt", {})

    assert res == "Attachment: attachment1"
    attached_objs = list(attachments)
    assert len(attached_objs) == 1
    assert attached_objs[0] == Attachment(
        id="attachment1",
        name="inline.txt",
        data=b'Attachment: {{ inline("inline.txt") }}\n',
        media_type="text/plain",
        attachment_type=AttachmentType.inline,
    )


def test_template_subject():
    subject = Subject("Original")
    attachments = Attachments(Path("tests/email/templates"))

    env = get_environment(Path("tests/email/templates"))
    res = render_template(env, subject, attachments, "subject.txt", {})
    assert str(subject) == "Subject"
    assert res == ("Subject is Original\n" "Subject is Subject\n" "Subject is Subject")


def test_template_subject_default():
    subject = Subject(None)
    attachments = Attachments(Path("tests/email/templates"))

    env = get_environment(Path("tests/email/templates"))
    res = render_template(env, subject, attachments, "subject_default.txt", {})

    assert str(subject) == "Subject"
    assert res == "Subject is Subject"

    subject = Subject("Original")
    attachments = Attachments(Path("tests/email/templates"))
    res = render_template(env, subject, attachments, "subject_default.txt", {})

    assert str(subject) == "Original"
    assert res == "Subject is Original"
