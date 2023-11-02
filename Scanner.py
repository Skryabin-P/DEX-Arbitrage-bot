from threading import Thread
from DEX.utils import exec_time
import itertools


class Scanner:
    def __init__(self, *exchanges):
        self.exchanges = exchanges

    def get_pairs(self):
        threads = []
        for exchange in self.exchanges:
            thread = Thread(target=exchange.pair_list)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    @exec_time
    def update_prices(self):
        threads = []
        for exchange in self.exchanges:
            thread = Thread(target=exchange.update_price_book())
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        for exchange in self.exchanges:
            print(exchange.price_book)

    def scan(self):
        while True:
            self.update_prices()
            for exchange1, exchange2 in itertools.combinations(self.exchanges, 2):
                common_pairs = set(exchange1.price_book.keys()).intersection(
                    set(exchange2.price_book.keys()))
                for pair in common_pairs:
                    ex1_prices = exchange1.price_book[pair]
                    ex2_prices = exchange2.price_book[pair]
                    profits = self.calculate_pair_profit(ex1_prices, ex2_prices)
                    print(f"Profit on {pair} from {exchange1.name} to {exchange2.name} is {profits[0]}")
                    print(f"Profit on {pair} from {exchange2.name} to {exchange1.name} is {profits[1]}")
            time.sleep(3)

    def calculate_pair_profit(self, ex1_prices, ex2_prices):
        ex1_to_ex2_profit = (ex2_prices['sell_price'] - ex1_prices['buy_price']) / ex1_prices['buy_price'] * 100
        ex2_to_ex1_profit = (ex1_prices['sell_price'] - ex2_prices['buy_price']) / ex2_prices['buy_price'] * 100
        return ex1_to_ex2_profit, ex2_to_ex1_profit


if __name__ == "__main__":
    from DEX.UniswapV2 import UniswapV2
    from DEX.UniswapV3 import UniswapV3
    from DEX.PancakeSwapV2 import PancakeSwapV2
    from DEX.PancakeSwapV3 import PancakeSwapV3
    from DEX.SushiSwapV2 import SushiSwapV2
    from DEX.SushiSwapV3 import SushiSwapV3

    import os
    from dotenv import load_dotenv
    import time

    load_dotenv()
    net = os.environ['INFURA_MAINNET']

    uniswap_v3 = UniswapV3(net, 500)
    uniswap_v2 = UniswapV2(net)
    sushi3 = SushiSwapV3(net, 500)
    scanner = Scanner(uniswap_v3, uniswap_v2, sushi3)

    scanner.scan()
    # sushi3.update_price_book()
    # print(sushi3.price_book)
    # uniswap_v3.update_price_book()
    #
    # print(uniswap_v3.price_book)
    # scanner.update_prices()
    # scan = Scanner(uniswap_v3, uniswap_v2)
    # scan.get_pairs()
