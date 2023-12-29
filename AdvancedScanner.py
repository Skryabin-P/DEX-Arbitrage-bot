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
                    # if pricebook1 == 'WMATIC-WETH' and pricebook2 == 'WMATIC-WETH':
                    #     print()
                    if pricebook1.split('-')[0] in pricebook2.split('-')[0]:
                        sec_vertex1 = f'{exchange2.name}_{pricebook2}_sell'
                    elif pricebook1.split('-')[0] in pricebook2.split('-')[1]:
                        sec_vertex1 = f'{exchange2.name}_{pricebook2}_buy'

                    if pricebook1.split('-')[1] in pricebook2.split('-')[1]:
                        sec_vertex2 = f'{exchange2.name}_{pricebook2}_buy'

                    elif pricebook1.split('-')[1] in pricebook2.split('-')[0]:
                        sec_vertex2 = f'{exchange2.name}_{pricebook2}_sell'
                # if sec_vertex1 == 'UniswapV3/3000_SUSHI-WETH_buy' or sec_vertex2 == 'UniswapV3/3000_SUSHI-WETH_buy':
                #     print(1)

                    if sec_vertex1:
                        edges.append((base_vertex1, sec_vertex1))
                    if sec_vertex2:
                        edges.append((base_vertex2, sec_vertex2))

        my_graph = DiGraph(edges)

        cycles = sorted(filter(lambda x: len(x) > 2, simple_cycles(my_graph, 4)))
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

        for index, step in enumerate(path):

            exchange_name, pair, action = step.split('_')
            exchange = self.find_exchange(exchange_name)
            step_price = exchange.price_book[pair][f'{action}_price']

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

            amount_in = amount_out

        profit = (amount_out - initial_amount) / initial_amount * 100
        if profit > -0.2:
            print(path)
            print(initial_amount)
            print(amount_out)
            print(f'Profit {profit}')
            print('---------------------------------')


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

    converter = Converter('USDC', 10)
    load_dotenv()
    net = "Polygon"
    subnet = "MAINNET"
    infura_api_key = os.environ['INFURA_API_KEY']
    ganache = "http://127.0.0.1:7545/"

    uniswap_v3_pools_3000 = ['WMATIC-WETH', 'WBTC-USDC', 'LINK-USDC','WBTC-USDC1', 'LINK-USDC1','WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC',
                             'LINK-WETH', 'WBTC-WETH', 'WMATIC-USDC', 'AAVE-WETH',
                             'VOXEL-USDC', 'WETH-USDC', 'WETH-USDT', 'UNI-WETH', 'UNI-USDC', 'UNI-USDT',
                             'SUSHI-WETH', 'LINK-WMATIC', 'USDC-USDC1']
    uniswap_v3_pools_500 = ['WETH-USDC', 'WBTC-WETH', 'WMATIC-USDC', 'WMATIC-WETH', 'WMATIC-USDC',
                            'WMATIC-USDT', 'WETH-USDC', 'WBTC-USDC', 'PAR-USDC',
                            'WBTC-USDC1', 'LINK-USDC1','WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC', 'USDC-USDC1']

    sushi3_pools_3000 = ['WETH-USDC', 'WBTC-USDC', 'SUSHI-WETH', 'WETH-USDT', 'MANA-WETH',
                         'WBTC-WETH', 'STG-USDC', 'AVAX-WETH', 'WMATIC-USDC', 'WMATIC-WETH',
                         'WMATIC-USDT', 'AAVE-WETH', 'WMATIC-DAI', 'WETH-DAI', 'BAL-USDC',
                         'MVI-USDT', 'SUSHI-USDC', 'CRV-WETH',  'LINK-WMATIC',
                         'WBTC-USDC1', 'LINK-USDC1','WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC', 'USDC-USDC1']
    sushi3_pools_500 = ['WMATIC-USDC', 'WMATIC-WETH', 'CGG-WETH', 'WETH-USDC', 'WMATIC-USDT',
                        'WMATIC-DAI', 'WBTC-USDT', 'WETH-DAI',
                        'WBTC-USDC1', 'LINK-USDC1','WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC', 'USDC-USDC1']

    sushi2_pairs = ['WMATIC-WETH', 'STG-USDC', 'NCT-USDC', 'KLIMA-USDC', 'WETH-USDC',
                    'WBTC-WETH', 'WETH-DAI', 'AAVE-WETH', 'WMATIC-USDC', 'LINK-WETH', 'WETH-USDT',
                    'AVAX-WETH', 'MANA-WETH', 'CRV-WETH', 'UNI-WETH', 'BAL-WETH',
                    'SUSHI-WETH', 'AAVE-WETH', 'UNI-USDC', 'UNI-WETH',  'LINK-WMATIC',
                    'WBTC-USDC1', 'LINK-USDC1','WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC', 'USDC-USDC1']

    uniswapV3_3000 = UniswapV3(net, subnet, infura_api_key, 3000, slippage=0.1)
    uniswapV3_3000.pair_list = uniswap_v3_pools_3000

    uniswapV3_500 = UniswapV3(net, subnet, infura_api_key, 500, slippage=0.1)
    uniswapV3_500.pair_list = uniswap_v3_pools_500

    sushi3_3000 = SushiSwapV3(net, subnet, infura_api_key, 3000, slippage=0.1)
    sushi3_3000.pair_list = sushi3_pools_3000

    sushi3_500 = SushiSwapV3(net, subnet, infura_api_key, 500, slippage=0.1)
    sushi3_500.pair_list = sushi3_pools_500

    sushi2 = SushiSwapV2(net, subnet, infura_api_key, slippage=0.1)
    sushi2.pair_list = sushi2_pairs

    # uniswapV3_3000.quote_asset_prices = converter.convert()
    #
    # uniswapV3_3000.update_price_book()
    # print(uniswapV3_3000.price_book)

    #
    # sushitoken = '0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a'
    # weth = '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
    # print(weth)
    # params = {
    #             "tokenIn": sushitoken,
    #             "tokenOut": weth,
    #             "amount": int(10**18),
    #             "fee": 3000,
    #             "sqrtPriceLimitX96": 0
    #         }
    #
    # print(params)
    #
    # result = uniswapV3_3000.quoter.functions.quoteExactOutputSingle(params).call()
    # print(result)
    # print(result[0] / 10**18)

    # uniswapV3_3000.update_price_book()
    #
    # print(uniswapV3_3000.price_book)

    scanner = Scanner([uniswapV3_500, uniswapV3_3000, sushi2, sushi3_500, sushi3_3000],
                      converter)

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
