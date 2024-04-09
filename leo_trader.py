from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import collections
from collections import defaultdict
import random
import math
import copy
import numpy as np

# eyJraWQiOiJ4M3NhZjFZTkNsRGwyVDljemdCR01ybnVVMlJlNDNjb1E1UGxYMWgwb2tBPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI0ZTBhZmE5Ny04ZDlmLTQ5MWMtOTM1YS00Njg2YmE3YThkZjMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LXdlc3QtMS5hbWF6b25hd3MuY29tXC9ldS13ZXN0LTFfek9mVngwcWl3IiwiY29nbml0bzp1c2VybmFtZSI6IjRlMGFmYTk3LThkOWYtNDkxYy05MzVhLTQ2ODZiYTdhOGRmMyIsIm9yaWdpbl9qdGkiOiI0OTAyMWNjMS04NDIwLTRmM2YtYTJkMC01MzI4Mzg4YzNmOWEiLCJhdWQiOiIzMmM1ZGM1dDFrbDUxZWRjcXYzOWkwcjJzMiIsImV2ZW50X2lkIjoiYmUwNTQ2MTgtYzM2NC00MDZhLWE4YjgtN2NjOTI4YzcxOTk2IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3MTI2Mzc2MTEsImV4cCI6MTcxMjY0ODQzNywiaWF0IjoxNzEyNjQ0ODM3LCJqdGkiOiI5YmRlZWU3Yy01ZmE5LTRjNzktOGIyYS1lNDdkNThhYjE1MzAiLCJlbWFpbCI6Imxlby5tYWtzeW1lbmtvQGJlcmtlbGV5LmVkdSJ9.o_UQvEEPmkX0JQmogs7L8-0AjsnzrOMNh3kZTS64nFXEYgW_pHeRZjLMNAqA3FNGcWgLnKF19G3b5UFdvwbIIuVXNCndl13_nYjQP5oFSO4HVHPjlukJ9Ttozu4bXHhw7QMIrZOJuIbp46rqY_dqvl0_ayEtcFCgWgXsXo9zr-SInLRLQtvzINT37tLT7rG79HpPGIIsbO32U0AZ7Fx5PFzVkCRiIn4J_gwqM3maTDMSdc__RL-FUbahpn8AD8Yu4BCikyMPHHAUqgNpPcjJU28txrJmOKvjxluJQ6HljigsVFfiWno3NIWnLt0u6gzGP1RnaNKz7HCOlf9SPFSPzQ
empty_dict = {'AMETHYSTS' : 0, 
            'STARFRUIT' : 0}


### UTILS
def def_value():
    return copy.deepcopy(empty_dict)

### CALCS


### TRADER
class Trader:

    POSITION_LIMIT = {'AMETHYSTS' : 20, 
                        'STARFRUIT' : 20}

    position = copy.deepcopy(empty_dict)
    volume_traded = copy.deepcopy(empty_dict)
    cpnl = defaultdict(lambda : 0)


    # UTILS
    def values_extract(self, order_dict, buy=0):
        tot_vol = 0
        best_val = -1
        mxvol = -1

        for ask, vol in order_dict.items():
            if(buy==0):
                vol *= -1
            tot_vol += vol
            if tot_vol > mxvol:
                mxvol = vol
                best_val = ask
        
        return tot_vol, best_val

    # STRATS
    def compute_orders_amethysts(self, product, order_depth, acc_bid, acc_ask):
        UNDERCUT = 1 # non-int values are not allowed?
        acc_bid = 10_000
        acc_ask = 10_000

        orders: list[Order] = []

        osell = collections.OrderedDict(sorted(order_depth.sell_orders.items()))
        obuy = collections.OrderedDict(sorted(order_depth.buy_orders.items(), reverse=True))

        sell_vol, best_sell_pr = self.values_extract(osell)
        buy_vol, best_buy_pr = self.values_extract(obuy, 1)

        cpos = self.position[product]

        mx_with_buy = -1

        for ask, vol in osell.items():
            if ((ask < acc_bid) or ((self.position[product]<0) and (ask == acc_bid))) and cpos < self.POSITION_LIMIT['AMETHYSTS']:
                mx_with_buy = max(mx_with_buy, ask)
                order_for = min(-vol, self.POSITION_LIMIT['AMETHYSTS'] - cpos)
                cpos += order_for
                assert(order_for >= 0)
                orders.append(Order(product, ask, order_for))

        # mprice_actual = (best_sell_pr + best_buy_pr)/2
        # mprice_ours = (acc_bid+acc_ask)/2

        undercut_buy = best_buy_pr + UNDERCUT
        undercut_sell = best_sell_pr - UNDERCUT
        
        # DONT GET THIS: prevents setting a buy above market middle - 1 (sorta a loss cap?)

        bid_pr = min(undercut_buy, acc_bid-1) # we will shift this by 1 to beat this price
        sell_pr = max(undercut_sell, acc_ask+1)

        # if we are short: more agressive buy
        if (cpos < self.POSITION_LIMIT['AMETHYSTS']) and (self.position[product] < 0):
            num = min(40, self.POSITION_LIMIT['AMETHYSTS'] - cpos)
            orders.append(Order(product, min(undercut_buy + 1, acc_bid-1), num))
            cpos += num

        # if we are long: less aggressive buying
        if (cpos < self.POSITION_LIMIT['AMETHYSTS']) and (self.position[product] > 15):
            num = min(40, self.POSITION_LIMIT['AMETHYSTS'] - cpos)
            orders.append(Order(product, min(undercut_buy - 1, acc_bid-1), num))
            cpos += num

        # normal buying
        if cpos < self.POSITION_LIMIT['AMETHYSTS']:
            num = min(40, self.POSITION_LIMIT['AMETHYSTS'] - cpos)
            orders.append(Order(product, bid_pr, num))
            cpos += num

        print("PAST THE BUYING", cpos)
        
        cpos = self.position[product]
        # DONT YET GET THIS
        for bid, vol in obuy.items():
            if ((bid > acc_ask) or ((self.position[product]>0) and (bid == acc_ask))) and cpos > -self.POSITION_LIMIT['AMETHYSTS']:
                order_for = max(-vol, -self.POSITION_LIMIT['AMETHYSTS']-cpos)
                # order_for is a negative number denoting how much we will sell
                cpos += order_for
                assert(order_for <= 0)
                orders.append(Order(product, bid, order_for))

        # if long: more agressive sell
        if (cpos > -self.POSITION_LIMIT['AMETHYSTS']) and (self.position[product] > 0):
            num = max(-40, -self.POSITION_LIMIT['AMETHYSTS']-cpos)
            orders.append(Order(product, max(undercut_sell-1, acc_ask+1), num))
            cpos += num

        # if very short: less aggressive sell
        if (cpos > -self.POSITION_LIMIT['AMETHYSTS']) and (self.position[product] < -15):
            num = max(-40, -self.POSITION_LIMIT['AMETHYSTS']-cpos)
            orders.append(Order(product, max(undercut_sell+1, acc_ask+1), num))
            cpos += num

        # normal sell
        if cpos > -self.POSITION_LIMIT['AMETHYSTS']:
            num = max(-40, -self.POSITION_LIMIT['AMETHYSTS']-cpos)
            orders.append(Order(product, sell_pr, num))
            cpos += num

        return orders



    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {'AMETHYSTS' : [], 'STARFRUIT' : [], }

        # Iterate over all the keys (the available products) contained in the order dephts
        for key, val in state.position.items():
            self.position[key] = val
        print()
        for key, val in self.position.items():
            print(f'{key} position: {val}')

        timestamp = state.timestamp

        pearls_lb = 10000
        pearls_ub = 10000

        # CHANGE FROM HERE

        # acc_bid = {'AMETHYSTS' : pearls_lb, 'STARFRUIT' : bananas_lb} # we want to buy at slightly below
        # acc_ask = {'AMETHYSTS' : pearls_ub, 'STARFRUIT' : bananas_ub} # we want to sell at slightly above


        order_depth: OrderDepth = state.order_depths['AMETHYSTS']
        # orders = self.compute_orders_amethysts('AMETHYSTS', order_depth, acc_bid[product], acc_ask[product])
        orders = self.compute_orders_amethysts('AMETHYSTS', order_depth, 10000, 10000)
        result['AMETHYSTS'] += orders

        # count pnl by product
        for product in state.own_trades.keys():
            for trade in state.own_trades[product]:
                if trade.timestamp != state.timestamp-100:
                    continue
                # print(f'We are trading {product}, {trade.buyer}, {trade.seller}, {trade.quantity}, {trade.price}')
                self.volume_traded[product] += abs(trade.quantity)
                if trade.buyer == "SUBMISSION":
                    self.cpnl[product] -= trade.quantity * trade.price
                else:
                    self.cpnl[product] += trade.quantity * trade.price

        totpnl = 0

        ##### DONT GET 
        for product in state.order_depths.keys():
            settled_pnl = 0
            best_sell = min(state.order_depths[product].sell_orders.keys())
            best_buy = max(state.order_depths[product].buy_orders.keys())

            if self.position[product] < 0:
                settled_pnl += self.position[product] * best_buy
            else:
                settled_pnl += self.position[product] * best_sell
            totpnl += settled_pnl + self.cpnl[product]
            print(f"For product {product}, {settled_pnl + self.cpnl[product]}, {(settled_pnl+self.cpnl[product])/(self.volume_traded[product]+1e-20)}")
        

        print(f"Timestamp {timestamp}, Total PNL ended up being {totpnl}")
        # print(f'Will trade {result}')
        print("End transmission")
        
        traderData = "SAMPLE" 
        conversions = 1
        return result, conversions, traderData