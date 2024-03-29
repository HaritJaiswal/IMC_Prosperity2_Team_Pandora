import math
import numpy as np
from typing import List, Tuple

from datamodel import OrderDepth, UserId, TradingState, Order

VWAP_DEPTH : int = 3
OFI_DEPTH : int = 3
TICK_SIZE : int = 1

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


def get_price_prediction(symbol : str, ob_list : List[OrderDepth], ) -> Tuple[float, float, float]:
    vwap = update_vwap(ob_list[-1])
    spread = 2
    
    return vwap, get_bid_price(vwap, spread, TICK_SIZE), get_ask_price(vwap, spread, TICK_SIZE)
    
    
    
    
    