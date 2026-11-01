import os
import unittest
from unittest import mock

from turkpin import TEST_URL, LIVE_URL, TurkpinClient

try:
    import django
except ImportError:
    django = None
try:
    import flask
except ImportError:
    flask = None
try:
    import fastapi
except ImportError:
    fastapi = None

ENV = {"TURKPIN_USERNAME": "dealer@example.com", "TURKPIN_PASSWORD": "secret", "TURKPIN_TEST": "true"}


class FromEnvTest(unittest.TestCase):
    def test_from_env(self):
        with mock.patch.dict(os.environ, dict(ENV, TURKPIN_TIMEOUT="5")):
            c = TurkpinClient.from_env()
        self.assertEqual(c.url, TEST_URL)
        self.assertEqual(c.timeout, 5)

    def test_missing_credentials(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                TurkpinClient.from_env()


@unittest.skipIf(django is None, "django not installed")
class DjangoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django.conf import settings
        if not settings.configured:
            settings.configure(TURKPIN={"USERNAME": "dealer@example.com", "PASSWORD": "secret", "TEST": True})
            django.setup()

    def test_get_client(self):
        from django.test import override_settings
        from turkpin.contrib.django import get_client
        with override_settings(TURKPIN={"USERNAME": "u", "PASSWORD": "p", "TEST": True}):
            c = get_client()
            self.assertIs(c, get_client())
            self.assertEqual(c.url, TEST_URL)
        with override_settings(TURKPIN={"USERNAME": "u", "PASSWORD": "p"}):
            self.assertEqual(get_client().url, LIVE_URL)

    def test_improperly_configured(self):
        from django.core.exceptions import ImproperlyConfigured
        from django.test import override_settings
        from turkpin.contrib.django import get_client
        with override_settings(TURKPIN={"USERNAME": "u"}):
            with self.assertRaises(ImproperlyConfigured):
                get_client()


@unittest.skipIf(flask is None, "flask not installed")
class FlaskTest(unittest.TestCase):
    def test_extension(self):
        from turkpin.contrib.flask import Turkpin
        app = flask.Flask(__name__)
        app.config.update(TURKPIN_USERNAME="u", TURKPIN_PASSWORD="p", TURKPIN_TEST=True)
        ext = Turkpin()
        ext.init_app(app)
        with app.app_context():
            self.assertIsInstance(ext.client, TurkpinClient)
            self.assertEqual(ext.client.url, TEST_URL)


@unittest.skipIf(fastapi is None, "fastapi not installed")
class FastAPITest(unittest.TestCase):
    def test_dependency(self):
        from fastapi import Depends, FastAPI
        from fastapi.testclient import TestClient
        from turkpin.contrib.fastapi import get_turkpin

        app = FastAPI()

        @app.get("/url")
        def url(turkpin: TurkpinClient = Depends(get_turkpin)):
            return {"url": turkpin.url}

        get_turkpin.cache_clear()
        with mock.patch.dict(os.environ, ENV):
            res = TestClient(app).get("/url")
        get_turkpin.cache_clear()
        self.assertEqual(res.json(), {"url": TEST_URL})


if __name__ == "__main__":
    unittest.main()
