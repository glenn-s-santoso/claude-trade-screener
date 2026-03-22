"""Shared Bybit HTTP session singleton."""

import os
import sys
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv()

_session: HTTP | None = None
_testnet: bool | None = None


def get_session(testnet: bool = False) -> HTTP:
    """Return a cached HTTP session, creating one if needed or if testnet mode changes."""
    global _session, _testnet
    if _session is None or _testnet != testnet:
        api_key = os.environ.get("BYBIT_API_KEY") or sys.exit("Error: BYBIT_API_KEY not set in environment or .env")
        api_secret = os.environ.get("BYBIT_API_SECRET") or sys.exit("Error: BYBIT_API_SECRET not set in environment or .env")
        _session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret,
        )
        _testnet = testnet
    return _session
