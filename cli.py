#!/usr/bin/env python3
"""
cli.py – Command-line interface for the Binance Futures Testnet Trading Bot.

Usage examples:
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000
  python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 62000 --stop-price 62500
"""

import argparse
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient, BinanceClientError, NetworkError
from bot.logging_config import setup_logging, get_logger
from bot.orders import OrderManager
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot – place MARKET, LIMIT, and STOP_LIMIT orders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000
  python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 62000 --stop-price 62500
        """,
    )
    parser.add_argument(
        "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol (e.g. BTCUSDT, ETHUSDT).",
    )
    parser.add_argument(
        "--side",
        required=True,
        metavar="SIDE",
        help="Order side: BUY or SELL.",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        metavar="TYPE",
        help="Order type: MARKET, LIMIT, or STOP_LIMIT.",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        metavar="QTY",
        help="Order quantity (e.g. 0.01).",
    )
    parser.add_argument(
        "--price",
        default=None,
        metavar="PRICE",
        help="Limit price – required for LIMIT and STOP_LIMIT orders.",
    )
    parser.add_argument(
        "--stop-price",
        dest="stop_price",
        default=None,
        metavar="STOP_PRICE",
        help="Stop trigger price – required for STOP_LIMIT orders.",
    )
    parser.add_argument(
        "--tif",
        dest="time_in_force",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT / STOP_LIMIT orders (default: GTC).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    return parser


def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
    time_in_force: str,
) -> None:
    """Print a formatted order request summary to stdout."""
    lines = [
        "",
        "═" * 50,
        "  ORDER REQUEST SUMMARY",
        "═" * 50,
        f"  Symbol         : {symbol}",
        f"  Side           : {side}",
        f"  Order Type     : {order_type}",
        f"  Quantity       : {quantity}",
    ]
    if price is not None:
        lines.append(f"  Price          : {price}")
    if stop_price is not None:
        lines.append(f"  Stop Price     : {stop_price}")
    if order_type in ("LIMIT", "STOP_LIMIT"):
        lines.append(f"  Time-in-Force  : {time_in_force}")
    lines.append("═" * 50)
    lines.append("")
    print("\n".join(lines))


def main() -> None:
    """Main entry point – parse args, validate, and dispatch order."""
    parser = _build_parser()
    args = parser.parse_args()

    # ── Logging setup ──────────────────────────────────────────────────
    setup_logging(args.log_level)
    logger = get_logger("cli")

    # ── Load credentials ───────────────────────────────────────────────
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        print(
            "\n[ERROR] BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file.\n"
        )
        logger.error("Missing API credentials. Check your .env file.")
        sys.exit(1)

    # ── Input validation ───────────────────────────────────────────────
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        print(f"\n[VALIDATION ERROR] {exc}\n")
        logger.error("Validation error: %s", exc)
        sys.exit(1)

    logger.info(
        "Validated input | symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )

    # ── Print request summary ──────────────────────────────────────────
    _print_request_summary(symbol, side, order_type, quantity, price, stop_price, args.time_in_force)

    # ── Build client and place order ───────────────────────────────────
    try:
        client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
        manager = OrderManager(client)

        if order_type == "MARKET":
            result = manager.place_market_order(symbol, side, quantity)
        elif order_type == "LIMIT":
            result = manager.place_limit_order(
                symbol, side, quantity, price, args.time_in_force  # type: ignore[arg-type]
            )
        elif order_type == "STOP_LIMIT":
            result = manager.place_stop_limit_order(
                symbol, side, quantity, price, stop_price, args.time_in_force  # type: ignore[arg-type]
            )
        else:
            print(f"\n[ERROR] Unsupported order type: {order_type}\n")
            sys.exit(1)

    except BinanceClientError as exc:
        print(f"\n[API ERROR] {exc}\n")
        logger.error("BinanceClientError: code=%s msg=%s", exc.code, exc.message)
        sys.exit(1)
    except NetworkError as exc:
        print(f"\n[NETWORK ERROR] {exc}\n")
        logger.error("NetworkError: %s", exc)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"\n[UNEXPECTED ERROR] {exc}\n")
        logger.exception("Unexpected exception: %s", exc)
        sys.exit(1)

    # ── Print result ───────────────────────────────────────────────────
    print(result.display())
    print(f"\n  ✅  Order placed successfully! Order ID: {result.order_id}\n")
    logger.info(
        "Order success | orderId=%s status=%s executedQty=%s avgPrice=%s",
        result.order_id, result.status, result.executed_qty, result.avg_price,
    )


if __name__ == "__main__":
    main()
