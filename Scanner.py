from threading import Thread
from DEX.utils import exec_time
import itertools
from prettytable import PrettyTable
from DEX.Converter import Converter


class Scanner:
    def __init__(self, *exchanges):
        self.exchanges = exchanges
        self.converter = Converter('USDC', 1000)

    # def get_pairs(self):
    #     threads = []
    #     for exchange in self.exchanges:
    #         thread = Thread(target=exchange.pair_list)
    #         thread.start()
    #         threads.append(thread)
    #
    #     for thread in threads:
    #         thread.join()

    def update_quote_asset_prices(self):
        self.exchanges[0].quote_asset_prices = self.converter.convert()

    # @exec_time
    def update_prices(self):
        threads = []
        for exchange in self.exchanges:
            thread = Thread(target=exchange.update_price_book())
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        # for exchange in self.exchanges:
        #     print(exchange.price_book)

    def scan(self):
        # self.get_pairs()

        while True:
            self.update_quote_asset_prices()
            self.update_prices()
            self.arbitrage_spreads = []
            for exchange1, exchange2 in itertools.combinations(self.exchanges, 2):
                common_pairs = set(exchange1.price_book.keys()).intersection(
                    set(exchange2.price_book.keys()))
                for pair in common_pairs:
                    ex1_prices = exchange1.price_book[pair]
                    ex2_prices = exchange2.price_book[pair]
                    profits = self.calculate_pair_profit(ex1_prices, ex2_prices)
                    # if profits[0] >=0:
                    self.arbitrage_spreads.append([pair, exchange1.name, exchange2.name,
                                                   ex1_prices['buy_price'], ex1_prices['buy_amount'],
                                                   ex2_prices['sell_price'], ex2_prices['sell_amount'],
                                                   profits[0]])
                    # if profits[1] >= 0:
                    self.arbitrage_spreads.append([pair, exchange2.name, exchange1.name,
                                                   ex2_prices['buy_price'], ex2_prices['buy_amount'],
                                                   ex1_prices['sell_price'], ex1_prices['sell_amount'],
                                                   profits[1]])

            self.print_arbitrage_table()
            # print(f"Profit on {pair} from {exchange1.name} to {exchange2.name} is {profits[0]}")
            # print(f"Profit on {pair} from {exchange2.name} to {exchange1.name} is {profits[1]}")
            time.sleep(3)

    def calculate_pair_profit(self, ex1_prices, ex2_prices):
        ex1_to_ex2_profit = (ex2_prices['sell_price'] - ex1_prices['buy_price']) / ex1_prices['buy_price'] * 100
        ex2_to_ex1_profit = (ex1_prices['sell_price'] - ex2_prices['buy_price']) / ex2_prices['buy_price'] * 100
        return ex1_to_ex2_profit, ex2_to_ex1_profit

    def print_arbitrage_table(self):
        arbitrage_table = PrettyTable()
        arbitrage_table.field_names = ["Pair", "Exchange from", "Exchange to",
                                       "Buy price", "buy amount", "Sell price", "sell amount", "Profit %"]
        arbitrage_table.sortby = 'Profit %'

        arbitrage_table.add_rows(self.arbitrage_spreads)

        print(arbitrage_table)


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
    net = "Ethereum"
    subnet = "MAINNET"
    infura_api_key = os.environ['INFURA_API_KEY']

    pairs = ['WETH-usdc', 'AAVE-WETH', 'AAVE-USDC', 'WETH-USDT', 'WETH-DAI', 'WBTC-WETH', 'LINK-WETH', 'LINK-USDC', 'LINK-USDT']

    uniswap_v3 = UniswapV3(net, subnet, infura_api_key, 500)
    uniswap_v3.pair_list = pairs
    uniswap_v2 = UniswapV2(net, subnet, infura_api_key)
    uniswap_v2.pair_list = pairs
    sushi3 = SushiSwapV3(net, subnet, infura_api_key, 500)
    sushi3.pair_list = pairs
    sushi2 = SushiSwapV2(net, subnet, infura_api_key)
    sushi2.pair_list = pairs
    pancakeswap_v2 = PancakeSwapV2(net, subnet, infura_api_key)
    pancakeswap_v2.pair_list = pairs
    pancakeswap_v3 = PancakeSwapV3(net, subnet, infura_api_key, 500)
    pancakeswap_v3.pair_list = pairs
    scanner = Scanner(uniswap_v3,  sushi3, sushi2, pancakeswap_v2, pancakeswap_v3)

    scanner.scan()
    # sushi3.update_price_book()
    # print(sushi3.price_book)
    # uniswap_v3.update_price_book()
    #
    # print(uniswap_v3.price_book)
    # scanner.update_prices()
    # scan = Scanner(uniswap_v3, uniswap_v2)
    # scan.get_pairs()

    # TODO: Think about auto refreshable arbitrage table
