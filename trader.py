from typing import List
import string

from datamodel import OrderDepth, UserId, TradingState, Order
from prediciton import get_price_prediction
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
            acceptable_price, bid_price, ask_price = get_price_prediction(product, self.symbol_ob_collection[product]);  # Participant should calculate this value
            
            print(f'===== TS={state.timestamp} : STRATEGY FOR SYMBOL={product} =====')
            print(f"acceptable_price={acceptable_price}, bid_price={bid_price}, ask_price={ask_price}")
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
            print(f'buy_book={order_depth.buy_orders.items()}')
            print(f'sell_book={order_depth.sell_orders.items()}')
    
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