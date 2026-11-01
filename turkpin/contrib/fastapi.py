"""FastAPI dependency.

Reads TURKPIN_USERNAME, TURKPIN_PASSWORD, TURKPIN_TEST and TURKPIN_TIMEOUT from the environment once.
TurkpinClient is synchronous, so use it from plain ``def`` endpoints (FastAPI runs them in a thread pool)::

    from fastapi import Depends, FastAPI
    from turkpin import TurkpinClient
    from turkpin.contrib.fastapi import get_turkpin

    app = FastAPI()

    @app.get("/balance")
    def balance(turkpin: TurkpinClient = Depends(get_turkpin)):
        return {"balance": str(turkpin.get_balance().balance)}

Override in tests with ``app.dependency_overrides[get_turkpin] = lambda: fake_client``.
"""

from functools import lru_cache

from ..client import TurkpinClient


@lru_cache(maxsize=1)
def get_turkpin() -> TurkpinClient:
    return TurkpinClient.from_env()
