"""App module."""
import argparse
import contextlib
import logging
from pathlib import Path

import uvicorn
from loguru import logger
from quart import Quart

from oes.webhooks.email.template import get_environment
from oes.webhooks.log import setup_logging
from oes.webhooks.settings import Settings, load_settings

app = Quart(__name__)


def run():
    """Main entry point."""
    args = parse_args()
    settings = load_settings(args.config)
    setup_logging(args.debug)

    log_startup_summary(settings)
    uvicorn.run(
        "oes.webhooks.app:_get_app",
        factory=True,
        workers=args.workers,
        reload=args.reload,
        host=args.bind,
        port=args.port,
        log_level=logging.DEBUG if args.debug else None,
        log_config=None,
    )


def _get_app():
    args = parse_args()
    settings = load_settings(args.config)
    setup_logging(args.debug)
    return configure_app(settings)


def configure_app(settings):
    """Configure and return the app."""
    app.config["settings"] = settings
    app.config["email_template_env"] = get_environment(settings.email.template_path)

    with contextlib.suppress(ImportError):
        from oes.webhooks.sheets.client import GoogleSheetsClient

        if settings.google.service_account_credentials:
            app.config["sheets_client"] = GoogleSheetsClient(
                settings.google.service_account_credentials
            )

    import oes.webhooks.email.views  # noqa
    import oes.webhooks.sheets.views  # noqa

    return app


def log_startup_summary(settings: Settings):
    """Print startup information to the logger."""
    features = {
        "email": f"<green>enabled</green>, using {settings.email.use}"
        if settings.email.use
        else False,
        "sheets": "<green>enabled</green>"
        if settings.google.service_account_credentials
        and len(settings.google.sheets_hooks) > 0
        else False,
    }

    f = {k: v if v else "<d>not enabled</d>" for k, v in features.items()}

    logger.opt(colors=True).info(
        "Feature summary:\n\n<normal>"
        f"\tEmail:\t{f['email']}\n"
        f"\tSheets:\t{f['sheets']}\n"
        "</normal>"
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
        default="0.0.0.0",
        help="addresses to bind to",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8002, help="port to listen on"
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
