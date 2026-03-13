"""
Order placement logic for Binance Futures Testnet.

This module sits between the CLI layer and the raw API client.
It builds correct parameter dicts for each order type and returns
a normalised OrderResult dataclass.
"""

from dataclasses import dataclass, field
from typing import Optional

from bot.client import BinanceFuturesClient
from bot.logging_config import get_logger

logger = get_logger("orders")


@dataclass
class OrderResult:
    """Normalised representation of a Binance order response."""

    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    price: Optional[str] = None
    avg_price: Optional[str] = None
    orig_qty: Optional[str] = None
    executed_qty: Optional[str] = None
    time_in_force: Optional[str] = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> "OrderResult":
        """Build an OrderResult from a raw Binance API response dict."""
        return cls(
            order_id=data.get("orderId"),
            client_order_id=data.get("clientOrderId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("type"),
            status=data.get("status"),
            price=data.get("price"),
            avg_price=data.get("avgPrice"),
            orig_qty=data.get("origQty"),
            executed_qty=data.get("executedQty"),
            time_in_force=data.get("timeInForce"),
            raw=data,
        )

    def display(self) -> str:
        """Return a formatted multi-line summary string."""
        lines = [
            "─" * 50,
            "  ORDER RESPONSE",
            "─" * 50,
            f"  Order ID       : {self.order_id}",
            f"  Client Order ID: {self.client_order_id}",
            f"  Symbol         : {self.symbol}",
            f"  Side           : {self.side}",
            f"  Type           : {self.order_type}",
            f"  Status         : {self.status}",
            f"  Price          : {self.price}",
            f"  Avg Price      : {self.avg_price}",
            f"  Orig Qty       : {self.orig_qty}",
            f"  Executed Qty   : {self.executed_qty}",
            f"  Time In Force  : {self.time_in_force}",
            "─" * 50,
        ]
        return "\n".join(lines)


class OrderManager:
    """
    High-level order manager.

    Wraps BinanceFuturesClient to provide type-specific order placement
    methods (market, limit, stop-limit) with consistent logging.
    """

    def __init__(self, client: BinanceFuturesClient) -> None:
        """
        Args:
            client: An authenticated BinanceFuturesClient instance.
        """
        self.client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_request_summary(self, order_type: str, params: dict) -> None:
        """Log a human-readable request summary."""
        safe = {k: v for k, v in params.items()}
        logger.info("[%s] Placing order: %s", order_type, safe)

    def _place(self, params: dict) -> OrderResult:
        """
        Send the order to the exchange and return a normalised OrderResult.

        Args:
            params: Fully built Binance order parameter dict.

        Returns:
            Normalised OrderResult instance.
        """
        self._log_request_summary(params.get("type", "UNKNOWN"), params)
        raw = self.client.place_order(params)
        logger.info("Order placed successfully. Raw response: %s", raw)
        return OrderResult.from_response(raw)

    # ------------------------------------------------------------------
    # Public order methods
    # ------------------------------------------------------------------

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> OrderResult:
        """
        Place a MARKET order.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT').
            side: 'BUY' or 'SELL'.
            quantity: Order quantity.

        Returns:
            Normalised OrderResult.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }
        logger.info(
            "Market order request | symbol=%s side=%s qty=%s",
            symbol, side, quantity,
        )
        return self._place(params)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        """
        Place a LIMIT order.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT').
            side: 'BUY' or 'SELL'.
            quantity: Order quantity.
            price: Limit price.
            time_in_force: 'GTC' (default), 'IOC', or 'FOK'.

        Returns:
            Normalised OrderResult.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": time_in_force,
        }
        logger.info(
            "Limit order request | symbol=%s side=%s qty=%s price=%s tif=%s",
            symbol, side, quantity, price, time_in_force,
        )
        return self._place(params)

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        """
        Place a STOP_MARKET / STOP order (Stop-Limit on Binance Futures).

        Binance Futures uses type=STOP for stop-limit orders.

        Args:
            symbol: Trading pair (e.g. 'BTCUSDT').
            side: 'BUY' or 'SELL'.
            quantity: Order quantity.
            price: Limit price (activated once stopPrice is hit).
            stop_price: Trigger price.
            time_in_force: 'GTC' (default), 'IOC', or 'FOK'.

        Returns:
            Normalised OrderResult.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
            "timeInForce": time_in_force,
        }
        logger.info(
            "Stop-Limit order request | symbol=%s side=%s qty=%s price=%s stopPrice=%s tif=%s",
            symbol, side, quantity, price, stop_price, time_in_force,
        )
        return self._place(params)
