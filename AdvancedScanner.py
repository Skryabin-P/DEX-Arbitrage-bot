from threading import Thread
from DEX.utils import exec_time
import itertools
from prettytable import PrettyTable
from DEX.Converter import Converter
from networkx import DiGraph, simple_cycles


class Scanner:
    def __init__(self, exchanges, converter):
        self.exchanges = exchanges
        self.converter = converter

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

        self.update_quote_asset_prices()
        self.update_prices()
        self.arbitrage_spreads = []
        edges = []
        for exchange1, exchange2 in itertools.permutations(self.exchanges, 2):

            for pricebook1 in exchange1.price_book:
                base_vertex1 = f'{exchange1.name}_{pricebook1}_buy'
                sec_vertex1 = None
                base_vertex2 = f'{exchange1.name}_{pricebook1}_sell'
                sec_vertex2 = None
                for pricebook2 in exchange2.price_book:
                    if pricebook1.split('-')[0] in pricebook2.split('-')[0]:
                        sec_vertex1 = f'{exchange2.name}_{pricebook2}_sell'
                    elif pricebook1.split('-')[0] in pricebook2.split('-')[1]:
                        sec_vertex1 = f'{exchange2.name}_{pricebook2}_buy'

                    if pricebook1.split('-')[1] in pricebook2.split('-')[1]:
                        sec_vertex2 = f'{exchange2.name}_{pricebook2}_buy'

                    elif pricebook1.split('-')[1] in pricebook2.split('-')[0]:
                        sec_vertex2 = f'{exchange2.name}_{pricebook2}_sell'

                if sec_vertex1:
                    edges.append((base_vertex1, sec_vertex1))
                if sec_vertex2:
                    edges.append((base_vertex2, sec_vertex2))

        my_graph = DiGraph(edges)

        cycles = sorted(filter(lambda x: len(x) > 2, simple_cycles(my_graph, 6)))
        for cycle in cycles:
            self.calculate_path_income(cycle)
        # for vertex in edges:
        #     print(vertex)

    def find_exchange(self, name):
        for exchange in self.exchanges:
            if exchange.name == name:
                return exchange
        return None

    def calculate_path_income(self, path):
        initial_amount = None
        amount_in = None
        print(path)
        for index, step in enumerate(path):
            print(step)
            exchange_name, pair, action = step.split('_')
            exchange = self.find_exchange(exchange_name)
            step_price = exchange.price_book[pair][f'{action}_price']
            print(step_price)

            if action == 'buy':
                if index == 0:

                    initial_amount = exchange.price_book[pair][f'{action}_amount'] * step_price
                    amount_in = initial_amount
                amount_out = amount_in / step_price
            else:
                if index == 0:
                    amount_in = exchange.price_book[pair][f'{action}_amount']
                    initial_amount = amount_in
                amount_out = amount_in * step_price
            print(amount_out)
            amount_in = amount_out
            print('---------------------------')
        print(initial_amount)
        print(amount_out)
        print(f'Profit {((amount_out - initial_amount) / initial_amount) * 100}')






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

    converter = Converter('USDC', 1000)
    load_dotenv()
    net = "Ethereum"
    subnet = "MAINNET"
    infura_api_key = os.environ['INFURA_API_KEY']
    ganache = "http://127.0.0.1:7545/"
    pairs = ['WETH-USDC', 'AAVE-WETH', 'AAVE-USDC', 'WETH-USDT', 'WETH-DAI', 'WBTC-WETH', 'LINK-WETH',
             'LINK-USDC', 'LINK-USDT',
             'WBTC-USDT', 'WBTC-USDC']

    uniswap_v3 = UniswapV3(net, subnet, infura_api_key, 500, ganache, 0.1)
    uniswap_v3.pair_list = pairs
    uniswap_v2 = UniswapV2(net, subnet, infura_api_key, ganache, 0.1)
    uniswap_v2.pair_list = pairs
    sushi3 = SushiSwapV3(net, subnet, infura_api_key, 500, ganache, 0.1)
    sushi3.pair_list = pairs
    sushi2 = SushiSwapV2(net, subnet, infura_api_key, ganache, 0.1)
    sushi2.pair_list = pairs
    pancakeswap_v2 = PancakeSwapV2(net, subnet, infura_api_key, ganache, 0.1)
    pancakeswap_v2.pair_list = pairs
    pancakeswap_v3 = PancakeSwapV3(net, subnet, infura_api_key, 500, ganache, 0.1)
    pancakeswap_v3.pair_list = pairs
    scanner = Scanner([uniswap_v3, sushi3, sushi2, pancakeswap_v2, pancakeswap_v3], converter)

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
