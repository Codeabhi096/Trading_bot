"""
Input validation for trading bot CLI arguments.
All validators raise ValueError with a human-readable message on failure.
"""

from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a trading symbol.

    Args:
        symbol: Raw symbol string from the user (e.g. 'btcusdt').

    Returns:
        Upper-cased symbol string.

    Raises:
        ValueError: If the symbol is empty or contains invalid characters.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValueError(
            f"Invalid symbol '{symbol}'. Only alphanumeric characters are allowed (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Upper-cased side string.

    Raises:
        ValueError: If side is not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET', 'LIMIT', or 'STOP_LIMIT' (case-insensitive).

    Returns:
        Upper-cased order type string.

    Raises:
        ValueError: If order type is not supported.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> float:
    """
    Validate order quantity.

    Args:
        quantity: String representation of the quantity.

    Returns:
        Positive float quantity.

    Raises:
        ValueError: If quantity is not a positive number.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate order price based on order type.

    For LIMIT and STOP_LIMIT orders a positive price is required.
    For MARKET orders price must be None / not supplied.

    Args:
        price: String representation of the price, or None.
        order_type: Already-validated order type string.

    Returns:
        Positive float price, or None for MARKET orders.

    Raises:
        ValueError: If price requirements are not met.
    """
    if order_type == "MARKET":
        if price is not None:
            raise ValueError("Price should not be specified for MARKET orders.")
        return None

    # LIMIT and STOP_LIMIT require a price
    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")
    return p


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate stop price (only required for STOP_LIMIT orders).

    Args:
        stop_price: String representation of the stop price, or None.
        order_type: Already-validated order type string.

    Returns:
        Positive float stop price for STOP_LIMIT, else None.

    Raises:
        ValueError: If stop price is required but missing or invalid.
    """
    if order_type != "STOP_LIMIT":
        return None
    if stop_price is None:
        raise ValueError("Stop price (--stop-price) is required for STOP_LIMIT orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero, got {sp}.")
    return sp
