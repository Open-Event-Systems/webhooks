"""HTML module."""
import css_inline
from minify_html import minify_html

inliner = css_inline.CSSInliner()


def process_html(html: str) -> str:
    """Minify HTML and inline CSS styles."""
    inlined = inliner.inline(html)
    minified = minify_html.minify(
        inlined,
        do_not_minify_doctype=True,
        ensure_spec_compliant_unquoted_attribute_values=True,
        keep_spaces_between_attributes=True,
    )
    return minified
