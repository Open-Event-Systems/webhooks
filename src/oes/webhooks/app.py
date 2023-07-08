"""App module."""
import argparse
from pathlib import Path

import uvicorn
from quart import Quart

from oes.webhooks.email.template import get_loader
from oes.webhooks.settings import load_settings

app = Quart(__name__)


def get_app():
    """Configure and return the app."""
    args = parse_args()
    settings = load_settings(args.config)

    app.config["settings"] = settings
    app.config["email_template_loader"] = get_loader(settings.email.template_path)
    return app


def run():
    """Main entry point."""
    args = parse_args()
    uvicorn.run(
        "oes.webhooks.app:get_app",
        factory=True,
        host=args.bind,
        port=args.port,
    )


def parse_args():
    """Parse the command line args."""
    parser = argparse.ArgumentParser(description="OES webhooks server")
    parser.add_argument(
        "-c", "--config", type=Path, required=False, help="path to a config file"
    )
    parser.add_argument(
        "-b", "--bind", type=str, default="0.0.0.0", help="address to listen on"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8002, help="port to listen on"
    )

    return parser.parse_args()


import oes.webhooks.email.views  # noqa
