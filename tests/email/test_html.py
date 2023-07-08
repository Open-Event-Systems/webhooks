from oes.webhooks.email.html import process_html

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Test</title>
        <style>
            .test {
                font-weight: bold;
            }

            a {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Test</h1>
        <p>
            Test <a style="color: red" href="#">link</a>.
        </p>
    </body>
</html>
"""

expected = (
    "<!doctype html><title>Test</title><body><h1>Test</h1><p>"
    'Test <a style="color: red;text-decoration: underline" href=#>link</a>.'
)


def test_process_html():
    res = process_html(html)
    assert res == expected
