from typing import List, Tuple
import string

from datamodel import OrderDepth, UserId, TradingState, Order

VWAP_DEPTH : int = 3
OFI_DEPTH : int = 3
TICK_SIZE : int = 1
MOMENTUM_WINDOW : int = 100

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

def get_bid_price(px, position, spread, tick) -> int:
    adjusted_px = px - (spread)# + max(0, position)/32)
    return int((adjusted_px//tick) * tick)

def get_ask_price(px, position, spread, tick) -> int:
    adjusted_px = px + (spread)# + max(0, -position)/32)
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

def get_price_prediction(symbol : str, ob_list : List[OrderDepth], position : int) -> Tuple[float, float, float]:
    spread = 1
    vwap = update_vwap(ob_list[-1])
    price_list = [update_vwap(ob) for ob in ob_list[-MOMENTUM_WINDOW:]]
    momentum = (price_list[-1] - sum(price_list)/len(price_list))/price_list[-1]
    
    
    return vwap, get_bid_price(vwap, position, spread, TICK_SIZE), get_ask_price(vwap, position, spread, TICK_SIZE)
    

class Trader:
    def __init__(self) -> None:
        self.symbol_ob_collection = {}
        
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            
            if product not in self.symbol_ob_collection:
                self.symbol_ob_collection[product] = []

            self.symbol_ob_collection[product].append(order_depth)
            
            if len(order_depth.sell_orders) == 0 or len(order_depth.buy_orders) == 0:
                continue ## if either the BUY book or the SELL book for the symbol is empty, we should not do anything
            
            ## acceptable_price = our signal, bid_price = price to BUY at, ask_price = price to SELL at
            acceptable_price, bid_price, ask_price = get_price_prediction(product, self.symbol_ob_collection[product], state.position.get(product,0));  # Participant should calculate this value
            
            print(f'===== TS={state.timestamp} : STRATEGY FOR SYMBOL={product} =====')
            print(f"acceptable_price={acceptable_price}, bid_price={bid_price}, ask_price={ask_price}")
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            print(f'buy_book={order_depth.buy_orders.items()}')
            print(f'sell_book={order_depth.sell_orders.items()}')
            print(f'position={state.position}')
    
            if len(order_depth.sell_orders) != 0:
                _, best_ask_amount = list(order_depth.sell_orders.items())[0]
                # if int(ask_price) < acceptable_price:
                print("BUY", str(-best_ask_amount) + "x", bid_price) ## BUY at bid_price and qty= qty present at TOP ASK
                orders.append(Order(product, bid_price, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                _, best_bid_amount = list(order_depth.buy_orders.items())[0]
                # if int(bid_price) > acceptable_price:
                print("SELL", str(best_bid_amount) + "x", ask_price) ## SELL at ask_price and qty= qty present at TOP BID
                orders.append(Order(product, ask_price, -best_bid_amount))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData