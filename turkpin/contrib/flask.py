"""Flask extension.

Config keys: TURKPIN_USERNAME, TURKPIN_PASSWORD, TURKPIN_TEST (default False), TURKPIN_TIMEOUT (default 30).

Usage::

    from turkpin.contrib.flask import Turkpin

    turkpin = Turkpin(app)        # or turkpin = Turkpin(); turkpin.init_app(app)

    @app.get("/games")
    def games():
        return [g.name for g in turkpin.client.get_games()]
"""

from typing import Optional

from flask import Flask, current_app

from ..client import TurkpinClient


class Turkpin:
    def __init__(self, app: Optional[Flask] = None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        app.config.setdefault("TURKPIN_TEST", False)
        app.config.setdefault("TURKPIN_TIMEOUT", 30)
        app.extensions["turkpin"] = TurkpinClient(
            app.config.get("TURKPIN_USERNAME", ""),
            app.config.get("TURKPIN_PASSWORD", ""),
            test=bool(app.config["TURKPIN_TEST"]),
            timeout=float(app.config["TURKPIN_TIMEOUT"]),
            base_url=app.config.get("TURKPIN_URL"),
        )

    @property
    def client(self) -> TurkpinClient:
        """Client of the current application."""
        return current_app.extensions["turkpin"]
