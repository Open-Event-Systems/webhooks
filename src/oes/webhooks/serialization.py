"""Serialization module."""
from cattrs.gen import make_dict_structure_fn
from cattrs.preconf.orjson import make_converter

from oes.webhooks.email.types import Email, EmailHookBody

converter = make_converter()


def make_structure_email_with_from(c, t):
    """Structure function for classes with a ``from`` field."""
    structure_dict = make_dict_structure_fn(t, c)

    def structure(v, t):
        if isinstance(v, dict):
            v = {**{k: v for k, v in v.items() if k != "from"}, "from_": v.get("from")}
        else:
            raise TypeError(f"Not a dict: {v}")
        return structure_dict(v, t)

    return structure


converter.register_structure_hook(
    Email, make_structure_email_with_from(converter, Email)
)
converter.register_structure_hook(
    EmailHookBody, make_structure_email_with_from(converter, EmailHookBody)
)
