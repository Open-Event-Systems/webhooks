"""App module."""
import argparse
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from pathlib import Path
from typing import Any, Optional, Union

import hypercorn
import uvloop
from hypercorn.run import run as hypercorn_run
from hypercorn.typing import ASGIFramework, ASGIReceiveCallable, ASGISendCallable, Scope
from loguru import logger
from quart import Quart

from oes.webhooks.email.template import get_environment
from oes.webhooks.log import setup_logging
from oes.webhooks.settings import Settings, load_settings

app = Quart(__name__)
_configured_app: Optional[ASGIFramework] = None


def run():
    """Main entry point."""
    global _configured_app
    args = parse_args()
    uvloop.install()

    asgi_config = hypercorn.Config.from_mapping(
        bind=args.bind or "0.0.0.0:8002",
        debug=args.debug,
        use_reloader=args.reload,
        workers=args.workers,
    )

    asgi_config.application_path = "oes.webhooks.app:_asgi_main"
    settings = load_settings(args.config)
    setup_logging(args.debug)

    log_startup_summary(args, settings)

    hypercorn_run(asgi_config)


async def _asgi_main(scope: Scope, recv: ASGIReceiveCallable, send: ASGISendCallable):
    global _configured_app
    if _configured_app is None:
        args = parse_args()
        settings = load_settings(args.config)
        setup_logging(args.debug)

        _configured_app = configure_app(settings)

    return await _configured_app(scope, recv, send)


def configure_app(settings: Settings) -> ASGIFramework:
    """Configure and return the app."""
    app.config["settings"] = settings
    app.config["email_template_env"] = get_environment(settings.email.template_path)

    wrapped = private_only_middleware(app)
    return wrapped


def private_only_middleware(app: ASGIFramework) -> ASGIFramework:
    """Middleware that only allows connections from internal networks."""

    async def sender(scope: Scope, recv: ASGIReceiveCallable, send: ASGISendCallable):
        if scope["type"] in ("http", "websocket"):
            _check_private_only(scope)

        await app(scope, recv, send)

    return sender


def _check_private_only(scope: Scope):
    host, _ = scope.get("client") or (None, None)
    if host and not _is_private_address(ip_address(host)):
        raise RuntimeError(f"Not allowing connection from non-private address {host}")


_private_networks = (
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("fd00::/8"),
    ip_network("::1/128"),
)


def _is_private_address(addr: Union[IPv4Address, IPv6Address]) -> bool:
    return any(addr in net for net in _private_networks)


def log_startup_summary(args: Any, settings: Settings):
    """Print startup information to the logger."""
    features = {
        "email": f"<green>enabled</green>, using {settings.email.use}"
        if settings.email.use
        else False
    }

    f = {k: v if v else "<d>not enabled</d>" for k, v in features.items()}

    logger.opt(colors=True).info(
        "Feature summary:\n\n<normal>" f"\tEmail:\t{f['email']}\n" "</normal>"
    )


def parse_args():
    """Parse the command line args."""
    parser = argparse.ArgumentParser(description="OES webhooks server")
    parser.add_argument(
        "-c", "--config", type=Path, required=False, help="path to a config file"
    )
    parser.add_argument(
        "-b",
        "--bind",
        type=str,
        action="append",
        default=[],
        help="addresses and ports to listen on",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False, help="enable debug logging"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=1, help="number of workers"
    )
    parser.add_argument(
        "--reload",
        default=False,
        action="store_true",
        help="reload on changes for development",
    )

    return parser.parse_args()


import oes.webhooks.email.views  # noqa
