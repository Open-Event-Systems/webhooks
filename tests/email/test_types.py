import re
from io import BytesIO

from oes.webhooks.email.types import (
    Attachment,
    AttachmentType,
    Email,
    _make_html_part,
    _make_text_part,
)


def test_make_attachment():
    att = Attachment(
        id="att1",
        name="test.txt",
        data=b"test-data",
        media_type="media/special",
        attachment_type=AttachmentType.attachment,
    )

    part = att.make_attachment()

    assert bytes(part) == (
        b"Content-Type: media/special\n"
        b"Content-Transfer-Encoding: base64\n"
        b'Content-Disposition: attachment; filename="test.txt"\n'
        b"Content-ID: <att1>\n"
        b"\n"
        b"dGVzdC1kYXRh\n"
    )


def test_make_text_part():
    part = _make_text_part("plain text")
    assert bytes(part) == (
        b'Content-Type: text/plain; charset="utf-8"\n'
        b"Content-Transfer-Encoding: 7bit\n"
        b"\n"
        b"plain text\n"
    )


def test_make_html_part():
    att = Attachment(
        id="att1",
        name="file.png",
        data=BytesIO(b"1234"),
        media_type="image/png",
        attachment_type=AttachmentType.inline,
    )
    html = "<b>html</b>"

    part = _make_html_part(html, [att])

    bytes_ = bytes(part)
    dec = bytes_.decode()
    sep = re.search(r"==+[0-9]+==", dec)
    assert sep
    sep_bytes = sep.group(0).encode()

    assert bytes_ == (
        b"Content-Type: multipart/related;\n"
        b' boundary="' + sep_bytes + b'"\n'
        b"\n"
        b"--" + sep_bytes + b"\n"
        b'Content-Type: text/html; charset="utf-8"\n'
        b"Content-Transfer-Encoding: 7bit\n"
        b"Content-Disposition: inline\n"
        b"\n"
        b"<b>html</b>\n"
        b"\n"
        b"--" + sep_bytes + b"\n"
        b"Content-Type: image/png\n"
        b"Content-Transfer-Encoding: base64\n"
        b'Content-Disposition: inline; filename="file.png"\n'
        b"Content-ID: <att1>\n"
        b"\n"
        b"MTIzNA==\n"
        b"\n"
        b"--" + sep_bytes + b"--\n"
    )


def test_make_message():
    att1 = Attachment(
        id="att1",
        name="file.png",
        data=BytesIO(b"1234"),
        media_type="image/png",
        attachment_type=AttachmentType.inline,
    )

    att2 = Attachment(
        id="att2",
        name="file.doc",
        data=BytesIO(b"1234"),
        media_type="application/octet-stream",
        attachment_type=AttachmentType.attachment,
    )

    email = Email(
        to="to@test.com",
        from_="from@test.com",
        subject="Subject",
        text="plain text",
        html="<b>HTML</b>",
        attachments=(att2, att1),
    )

    bytes_ = bytes(email.get_message())
    dec = bytes_.decode()
    seps = re.findall(r"==+[0-9]+==", dec)
    sep1 = seps[0].encode()
    sep2 = seps[2].encode()
    sep3 = seps[5].encode()

    assert bytes_ == (
        b'Content-Type: multipart/mixed; boundary="' + sep1 + b'"\n'
        b"From: from@test.com\n"
        b"To: to@test.com\n"
        b"Subject: Subject\n"
        b"\n"
        b"--" + sep1 + b"\n"
        b"Content-Type: multipart/alternative;\n"
        b' boundary="' + sep2 + b'"\n'
        b"\n"
        b"--" + sep2 + b"\n"
        b'Content-Type: text/plain; charset="utf-8"\n'
        b"Content-Transfer-Encoding: 7bit\n"
        b"\n"
        b"plain text\n"
        b"\n"
        b"--" + sep2 + b"\n"
        b"Content-Type: multipart/related;\n"
        b' boundary="' + sep3 + b'"\n'
        b"\n"
        b"--" + sep3 + b"\n"
        b'Content-Type: text/html; charset="utf-8"\n'
        b"Content-Transfer-Encoding: 7bit\n"
        b"Content-Disposition: inline\n"
        b"\n"
        b"<b>HTML</b>\n"
        b"\n"
        b"--" + sep3 + b"\n"
        b"Content-Type: image/png\n"
        b"Content-Transfer-Encoding: base64\n"
        b'Content-Disposition: inline; filename="file.png"\n'
        b"Content-ID: <att1>\n"
        b"\n"
        b"MTIzNA==\n"
        b"\n"
        b"--" + sep3 + b"--\n"
        b"\n"
        b"--" + sep2 + b"--\n"
        b"\n"
        b"--" + sep1 + b"\n"
        b"Content-Type: application/octet-stream\n"
        b"Content-Transfer-Encoding: base64\n"
        b'Content-Disposition: attachment; filename="file.doc"\n'
        b"Content-ID: <att2>\n"
        b"\n"
        b"MTIzNA==\n"
        b"\n"
        b"--" + sep1 + b"--\n"
    )
