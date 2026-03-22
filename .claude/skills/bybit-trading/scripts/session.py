"""Shared Bybit HTTP session singleton."""

import os
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv()

_session: HTTP | None = None
_testnet: bool | None = None


def get_session(testnet: bool = False) -> HTTP:
    """Return a cached HTTP session, creating one if needed or if testnet mode changes."""
    global _session, _testnet
    if _session is None or _testnet != testnet:
        _session = HTTP(
            testnet=testnet,
            api_key=os.environ["BYBIT_API_KEY"],
            api_secret=os.environ["BYBIT_API_SECRET"],
        )
        _testnet = testnet
    return _session
