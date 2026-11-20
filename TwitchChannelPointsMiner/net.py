"""Shared HTTP session: connection pooling without cross-request state."""
import threading
from http.cookiejar import DefaultCookiePolicy

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_local = threading.local()


def _build_session():
    session = requests.Session()
    # Retry only failures that happen before the request is sent (DNS/connect),
    # so POSTs (bets, claims) are never replayed.
    retry = Retry(total=None, connect=2, read=0, status=0, other=0, backoff_factor=0.5)
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # Module-level requests helpers never keep cookies; keep that behaviour.
    session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
    return session


def get_session():
    """One Session per thread (requests.Session is not guaranteed thread-safe)."""
    session = getattr(_local, "session", None)
    if session is None:
        session = _local.session = _build_session()
    return session
