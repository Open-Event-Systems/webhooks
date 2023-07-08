from pathlib import Path

from oes.webhooks.email.template import get_loader, render_template


def test_template():
    loader = get_loader(Path("tests/email/templates"))

    res = render_template(
        loader, "template.txt", {"subject": "Test", "text": "Test text."}
    )

    assert res == ("Test\n\nTest text.")
