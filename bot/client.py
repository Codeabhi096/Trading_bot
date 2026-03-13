"""
Binance Futures Testnet REST API client.

Handles authentication (HMAC-SHA256 signatures), request signing,
and low-level HTTP communication with the Binance Futures Testnet.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.logging_config import get_logger

logger = get_logger("client")

BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
MAX_RETRIES = 3


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error [{code}]: {message}")


class NetworkError(Exception):
    """Raised on network / connectivity failures."""


def _build_session() -> requests.Session:
    """
    Build a requests.Session with automatic retry logic.

    Retries on connection errors and 5xx responses (not on 4xx client errors).
    """
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST", "DELETE"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.

    Handles:
    - HMAC-SHA256 request signing
    - Timestamp injection
    - Structured logging of requests / responses / errors
    - Unified error handling
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL) -> None:
        """
        Initialise the client.

        Args:
            api_key: Binance API key.
            api_secret: Binance API secret.
            base_url: Base URL of the Binance Futures endpoint.
        """
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self._session = _build_session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceFuturesClient initialised. Base URL: %s", self.base_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for the given parameter dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret, query_string.encode(), hashlib.sha256
        ).hexdigest()
        return signature

    def _timestamp(self) -> int:
        """Return the current UTC timestamp in milliseconds."""
        return int(time.time() * 1000)

    # ------------------------------------------------------------------
    # Public HTTP methods
    # ------------------------------------------------------------------

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a signed or unsigned GET request.

        Args:
            endpoint: API path (e.g. '/fapi/v1/ping').
            params: Query parameters.
            signed: Whether to attach a timestamp + signature.

        Returns:
            Parsed JSON response as a dict.
        """
        params = params or {}
        if signed:
            params["timestamp"] = self._timestamp()
            params["signature"] = self._sign(params)
        url = f"{self.base_url}{endpoint}"
        logger.info("GET %s | params: %s", url, {k: v for k, v in params.items() if k != "signature"})
        try:
            resp = self._session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error on GET %s: %s", url, exc)
            raise NetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Timeout on GET %s: %s", url, exc)
            raise NetworkError(f"Request timed out: {exc}") from exc
        return self._handle_response(resp)

    def post(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a signed POST request.

        Args:
            endpoint: API path (e.g. '/fapi/v1/order').
            params: Form body parameters (automatically signed).

        Returns:
            Parsed JSON response as a dict.
        """
        params = params or {}
        params["timestamp"] = self._timestamp()
        params["signature"] = self._sign(params)
        url = f"{self.base_url}{endpoint}"
        safe_params = {k: v for k, v in params.items() if k != "signature"}
        logger.info("POST %s | body: %s", url, safe_params)
        try:
            resp = self._session.post(url, data=params, timeout=DEFAULT_TIMEOUT)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error on POST %s: %s", url, exc)
            raise NetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Timeout on POST %s: %s", url, exc)
            raise NetworkError(f"Request timed out: {exc}") from exc
        return self._handle_response(resp)

    def _handle_response(self, resp: requests.Response) -> Dict[str, Any]:
        """
        Parse the HTTP response and raise on errors.

        Args:
            resp: Raw requests.Response object.

        Returns:
            Parsed JSON body.

        Raises:
            BinanceClientError: On API-level errors (4xx / 5xx with JSON body).
            NetworkError: On non-JSON or unexpected HTTP errors.
        """
        logger.info(
            "Response HTTP %s | body: %s",
            resp.status_code,
            resp.text[:500],
        )
        try:
            data = resp.json()
        except ValueError:
            logger.error("Non-JSON response: %s", resp.text[:300])
            raise NetworkError(f"Unexpected non-JSON response (HTTP {resp.status_code}).")

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            code = data.get("code", -1)
            msg = data.get("msg", "Unknown error")
            logger.error("Binance API error: code=%s msg=%s", code, msg)
            raise BinanceClientError(code, msg)

        if not resp.ok:
            logger.error("HTTP error %s: %s", resp.status_code, resp.text[:300])
            raise NetworkError(f"HTTP error {resp.status_code}: {resp.text[:200]}")

        return data

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Test connectivity to the API. Returns True on success."""
        try:
            self.get("/fapi/v1/ping")
            logger.info("Ping successful.")
            return True
        except Exception as exc:
            logger.error("Ping failed: %s", exc)
            return False

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange info (symbol rules, lot size filters, etc.)."""
        return self.get("/fapi/v1/exchangeInfo")

    def place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new futures order.

        Args:
            params: Order parameters (symbol, side, type, quantity, price, …).

        Returns:
            Order response dict from Binance.
        """
        return self.post("/fapi/v1/order", params=params)
