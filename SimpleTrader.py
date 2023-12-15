import time

from DEX.UniswapV3 import UniswapV3
from DEX.UniswapV2 import UniswapV2
from DEX.SushiSwapV2 import SushiSwapV2
from DEX.SushiSwapV3 import SushiSwapV3
from DEX.PancakeSwapV3 import PancakeSwapV3
from DEX.PancakeSwapV2 import PancakeSwapV2
from DEX.Converter import Converter
from Scanner import Scanner
import json

class SimpleTrader:

    def __init__(self, *exchanges, converter):
        self.exchanges = exchanges
        self.scanner = Scanner(self.exchanges, converter=converter)

    def arbitrage(self):
        while True:
            self.scanner.scan()
            arbitrage_table = json.loads(self.scanner.arbitrage_data)
            if arbitrage_table[0]['Profit %'] > 0.6:
                pair = arbitrage_table[0]['Pair']
                for exchange in self.exchanges:
                    if exchange.name == arbitrage_table[0]['Exchange from']:
                        exchange_from = exchange
                    if exchange.name == arbitrage_table[0]['Exchange to']:
                        exchange_to = exchange
                exchange_from.encode_buy_order()
            time.sleep(10)





if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()

    network = "Polygon"
    subnet = "MAINNET"
    address = os.environ['address']
    private_key = os.environ['private_key']
    api_key = os.environ['INFURA_API_KEY']
    pair_list = ['WETH-usdc', 'AAVE-WETH', 'AAVE-USDC', 'WETH-USDT', 'WETH-DAI',
                 'WBTC-WETH', 'LINK-WETH', 'LINK-USDC', 'LINK-USDT',
                 'WMATIC-USDC', 'WMATIC-USDT', 'WMATIC-WETH', 'USDC-USDT']
    converter = Converter('USDC', 10)

    uniswapv3 = UniswapV3(network, subnet, api_key, 500, slippage=0.1)
    uniswapv3.pair_list = pair_list
    sushi2 = SushiSwapV2(network, subnet, api_key, slippage=0.1)
    sushi2.pair_list = pair_list
    sushi3 = SushiSwapV3(network, subnet, api_key, 500, slippage=0.1)
    sushi3.pair_list = pair_list
    trader = SimpleTrader(uniswapv3, sushi2, sushi3, converter=converter)
    trader.arbitrage()