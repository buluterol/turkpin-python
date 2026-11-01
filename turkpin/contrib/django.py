"""Django integration.

settings.py::

    TURKPIN = {
        "USERNAME": env("TURKPIN_USERNAME"),
        "PASSWORD": env("TURKPIN_PASSWORD"),
        "TEST": False,
        "TIMEOUT": 30,
    }

Usage::

    from turkpin.contrib.django import get_client
    games = get_client().get_games()
"""

import threading
from typing import Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import setting_changed

from ..client import TurkpinClient

_lock = threading.Lock()
_client: Optional[TurkpinClient] = None


def get_client() -> TurkpinClient:
    """Returns the shared client built from settings.TURKPIN."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                conf = getattr(settings, "TURKPIN", None)
                if not conf or not conf.get("USERNAME") or not conf.get("PASSWORD"):
                    raise ImproperlyConfigured("settings.TURKPIN must define USERNAME and PASSWORD")
                _client = TurkpinClient(
                    conf["USERNAME"],
                    conf["PASSWORD"],
                    test=bool(conf.get("TEST", False)),
                    timeout=float(conf.get("TIMEOUT", 30)),
                    base_url=conf.get("URL"),
                )
    return _client


def _reset(setting, **kwargs):
    global _client
    if setting == "TURKPIN":
        _client = None


setting_changed.connect(_reset)
