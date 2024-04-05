import math
import numpy as np
from typing import List, Tuple

from datamodel import OrderDepth, UserId, TradingState, Order

VWAP_DEPTH : int = 3
OFI_DEPTH : int = 3
TICK_SIZE : int = 1
MAX_SPREAD: int = 5

def min_qty(book : OrderDepth, level : int) -> int:
    ask_qty = 0
    ask_depth = len(book.sell_orders)
    level__ = min(level, ask_depth)
    sell_levels_list = list(book.sell_orders.items())

    for idx in range(level__):
        if idx >= ask_depth:
            break

        arr = sell_levels_list[idx]
        if float(-arr[1]) <= 0.0:
            level__ += 1
            continue
        ask_qty += float(-arr[1])

    bid_qty = 0
    bid_depth = len(book.buy_orders)
    level__ = min(level, bid_depth)
    buy_levels_list = list(book.buy_orders.items())

    for idx in range(level__):
        if idx >= bid_depth:
            break
        arr = buy_levels_list[idx]
        if float(arr[1]) <= 0.0:
            level__ += 1
            continue
        bid_qty += float(arr[1])

    return min(bid_qty, ask_qty)

def ask_vwap_qty(book : OrderDepth, level : int, qty : int) -> float:
    price__ = 0
    rem_qty = qty
    ask_depth = len(book.sell_orders)
    level__ = min(level, ask_depth)
    sell_levels_list = list(book.sell_orders.items())

    for idx in range(level__):
        if idx >= ask_depth:
            break
        arr = sell_levels_list[idx]
        if float(-arr[1]) <= 0.0:
            level__ += 1
            continue
        rem_qty -= float(-arr[1])
        if rem_qty <= 0:
            rem_qty += float(-arr[1])
            price__ += (float(arr[0]) * rem_qty)
            rem_qty = 0
            break
        else:
            price__ += (float(arr[0]) * float(-arr[1]))

    return (price__/qty)

def bid_vwap_qty(book : OrderDepth, level : int, qty : int) -> float:
    price__ = 0
    rem_qty = qty
    bid_depth = len(book.buy_orders)
    level__ = min(level, bid_depth)
    buy_levels_list = list(book.buy_orders.items())

    for idx in range(level__):
        if idx >= bid_depth:
            break
        arr = buy_levels_list[idx]
        if float(arr[1]) <= 0.0:
            level__ += 1
            continue
        rem_qty -= float(arr[1])
        if rem_qty <= 0:
            rem_qty += float(arr[1])
            price__ += (float(arr[0]) * rem_qty)
            rem_qty = 0
            break
        else:
            price__ += (float(arr[0]) * float(arr[1]))

    return (price__/qty)

def update_vwap(book : OrderDepth) -> float: # passing the book so that requests are minimised
    vol_wt_depth = VWAP_DEPTH
    qty = min_qty(book , vol_wt_depth)
    if qty <= 0:
        return 0.0

    assert (vol_wt_depth > 0)
    bid_to_use = bid_vwap_qty(book, vol_wt_depth, qty)
    ask_to_use = ask_vwap_qty(book, vol_wt_depth, qty)
    vwap__ = (bid_to_use + ask_to_use)/2.0

    return vwap__

def get_inventory_adjusted_min_dist(min_dist, inv) -> int:
    return min_dist + max(0, inv) * min_dist

def get_bid_price(px, spread, tick) -> int:
    adjusted_px = px - spread
    return int((adjusted_px//tick) * tick)

def get_ask_price(px, spread, tick) -> int:
    adjusted_px = px + spread
    truncated_px = (adjusted_px//tick) * tick

    if truncated_px < adjusted_px:
        return int(truncated_px + tick)
    else:
        return int(truncated_px)

def get_order_flow_imbalance(book: OrderDepth, depth: int) -> float:
    """
    Calculate the order flow imbalance (OFI) using the specified depth of the order book.
    The OFI is a measure of the excess of buy-side or sell-side pressure in the order book.

    Args:
        book (OrderDepth): The current order book state.
        depth (int): The number of levels to consider in the order book.

    Returns:
        float: The order flow imbalance value, positive for buy-side pressure, negative for sell-side pressure.
    """
    total_buy_volume = sum(float(vol) for price, vol in list(book.buy_orders.items())[:depth])
    total_sell_volume = sum(float(-vol) for price, vol in list(book.sell_orders.items())[:depth])

    total_volume = total_buy_volume + total_sell_volume
    if total_volume == 0:
        return 0.0

    ofi = (total_buy_volume - total_sell_volume) / total_volume
    return ofi

def get_price_prediction(symbol: str, ob_list: List[OrderDepth]) -> Tuple[float, float, float]:
    vwap = update_vwap(ob_list[-1])
    ofi = get_order_flow_imbalance(ob_list[-1], OFI_DEPTH)

    # Adjust the spread based on the OFI signal
    spread = 2  # Default spread value
    if ofi > 0.5:  # Strong buy-side pressure
        spread = max(1, spread - 1)  # Decrease spread
    elif ofi < -0.5:  # Strong sell-side pressure
        spread = min(MAX_SPREAD, spread + 1)  # Increase spread

    bid_price = get_bid_price(vwap, spread, TICK_SIZE)
    ask_price = get_ask_price(vwap, spread, TICK_SIZE)

    return vwap, bid_price, ask_price
