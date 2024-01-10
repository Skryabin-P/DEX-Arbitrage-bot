import time
from web3 import Web3
from asyncio import gather
from eth_abi import encode
from DEX.UniswapV3 import UniswapV3
from DEX.UniswapV2 import UniswapV2
from DEX.SushiSwapV2 import SushiSwapV2
from DEX.SushiSwapV3 import SushiSwapV3
from DEX.PancakeSwapV3 import PancakeSwapV3
from DEX.PancakeSwapV2 import PancakeSwapV2
from DEX.Converter import Converter
from DEX.utils import get_contract
from AdvancedScanner import AdvancedScanner
import json
from threading import Thread
import codecs
from operator import itemgetter


class AdvancedTrader:
    w3: Web3

    def __init__(self, *exchanges, converter, address, private_key, thd):
        self.exchanges = {exchange.name: exchange for exchange in exchanges}
        self.scanner = AdvancedScanner(self.exchanges, converter=converter)
        self.converter = converter
        self.address = address
        self.private_key = private_key
        self.w3 = exchanges[0].web3_client
        self.thd = thd
        self.quote_amount = converter.quote_amount
        self.arbitrage_contract = get_contract(self.w3, 'Arbitrage/Arbitrage',
                                               'Polygon', 'MAINNET')

    def arbitrage(self):
        while True:
            try:
                self.scanner.scan()
                spreads = sorted(self.scanner.arbitrage_spreads,
                                 key=itemgetter(1), reverse=True)
                if spreads[0][1] > self.thd:
                    print(f'Arbitrage opportunity found! '
                          f'\n {" -> ".join(spreads[0][0].keys())}'
                          f'\n Potential profit is {spreads[0][1]}%')
                    path = spreads[0][0]
                    amount_in = None
                    trades = []
                    approves = []
                    tokens = []
                    routers = []
                    remainder = 0
                    for index, (step, prices) in enumerate(path.items()):
                        trade, amount_out_min, approve, quote_asset, router = \
                            self.encode_trade(step, prices, amount_in)
                        print(amount_out_min)
                        print(prices)
                        print(amount_in)
                        print('-----------------------')
                        if index == 0:
                            flashloan_amount = int(prices[1] * 10**quote_asset.decimals)
                        remainder += 0.1
                        amount_in = amount_out_min
                        trades.append(trade)
                        approves.append(approve)
                        tokens.append(quote_asset.address)
                        routers.append(router)
                    encoded_data = encode(types=['address[]', 'bytes[]', 'address[]', 'bytes[]'],
                                          args=[routers, trades, tokens, approves])

                    min_income = (self.thd - remainder) / 100 * self.quote_amount + 100
                    self.prepare_tansaction()
                    gas = 250000 + 150000*len(trades)
                    if min_income > self.gas_price*gas * self.converter.matic_price / 10**18 * 1.05:
                        request_flashloan = self.arbitrage_contract.functions.requestFlashLoan(
                            tokens[0], flashloan_amount,
                            encoded_data).build_transaction({"chainId": self.chain_id,
                                                             "from": self.address, "gas": gas, "nonce": self.nonce,
                                                             'maxFeePerGas': int(self.gas_price * 1.05),
                                                             'maxPriorityFeePerGas': int(self.gas_price * 1)})
                        try:
                            signed_tx = self.w3.eth.account.sign_transaction(request_flashloan,
                                                                             private_key=self.private_key)

                            send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                            tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
                            print(tx_receipt)
                            time.sleep(1)
                            break
                            continue
                        except Exception as e:
                            print(e)
                    else:
                        print('Potential income do not worth transaction fee')


                time.sleep(10)

            except Exception as e:
                print('exception here')
                print(e)
                time.sleep(5)
                continue

    def encode_trade(self, step, prices, amount_in=None):
        exchange_name, pair, action = step.split('_')
        exchange = self.exchanges[exchange_name]
        if not amount_in:
            amount_in = prices[1]
        if action == 'buy':
            base_asset = exchange.pair_list[pair]['base_asset']
            quote_asset = exchange.pair_list[pair]['quote_asset']
            amount_out = amount_in / prices[0]
        else:
            base_asset = exchange.pair_list[pair]['quote_asset']
            quote_asset = exchange.pair_list[pair]['base_asset']
            amount_out = prices[0] * amount_in

        order, amount_out_min = exchange.encode_buy_order(
            base_asset, quote_asset, amount_in, amount_out)
        approve = exchange.encode_router_approve(quote_asset, amount_in)
        approve = codecs.decode(approve[2:], 'hex_codec')
        order = codecs.decode(order[2:], 'hex_codec')
        router_address = exchange.router.address
        return order, amount_out_min, approve, quote_asset, router_address

    def get_nonce(self):
        self.nonce = self.w3.eth.get_transaction_count(self.address)

    def get_chain_id(self):
        self.chain_id = self.w3.eth.chain_id

    def get_gas_price(self):
        self.gas_price = self.w3.eth.gas_price
    def prepare_tansaction(self):
        thread1 = Thread(target=self.get_nonce())
        thread2 = Thread(target=self.get_chain_id())
        thread3 = Thread(target=self.get_gas_price())

        thread1.start()
        thread2.start()
        thread3.start()

        thread1.join()
        thread2.join()
        thread3.join()

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
    uniswap_v3_pools_3000 = ['WMATIC-WETH', 'WBTC-USDC', 'LINK-USDC', 'WBTC-USDC1', 'LINK-USDC1', 'WMATIC-USDC',
                             'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC',
                             'LINK-WETH', 'WBTC-WETH', 'WMATIC-USDC', 'AAVE-WETH',
                             'VOXEL-USDC', 'WETH-USDC', 'WETH-USDT', 'UNI-WETH', 'UNI-USDC', 'UNI-USDT',
                             'SUSHI-WETH', 'LINK-WMATIC']
    uniswap_v3_pools_500 = ['WETH-USDC', 'WBTC-WETH', 'WMATIC-USDC', 'WMATIC-WETH', 'WMATIC-USDC',
                            'WMATIC-USDT', 'WETH-USDC', 'WBTC-USDC', 'PAR-USDC',
                            'WBTC-USDC1', 'LINK-USDC1', 'WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC']

    sushi3_pools_3000 = ['WETH-USDC', 'WBTC-USDC', 'SUSHI-WETH', 'WETH-USDT', 'MANA-WETH',
                         'WBTC-WETH', 'STG-USDC', 'AVAX-WETH', 'WMATIC-USDC', 'WMATIC-WETH',
                         'WMATIC-USDT', 'AAVE-WETH', 'WMATIC-DAI', 'WETH-DAI', 'BAL-USDC',
                         'MVI-USDT', 'SUSHI-USDC', 'CRV-WETH', 'LINK-WMATIC',
                         'WBTC-USDC1', 'LINK-USDC1', 'WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC']
    sushi3_pools_500 = ['WMATIC-USDC', 'WMATIC-WETH', 'CGG-WETH', 'WETH-USDC', 'WMATIC-USDT',
                        'WMATIC-DAI', 'WBTC-USDT', 'WETH-DAI',
                        'WBTC-USDC1', 'LINK-USDC1', 'WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC']

    sushi2_pairs = ['WMATIC-WETH', 'STG-USDC', 'NCT-USDC', 'KLIMA-USDC', 'WETH-USDC',
                    'WBTC-WETH', 'WETH-DAI', 'AAVE-WETH', 'WMATIC-USDC', 'LINK-WETH', 'WETH-USDT',
                    'AVAX-WETH', 'MANA-WETH', 'CRV-WETH', 'UNI-WETH', 'BAL-WETH',
                    'SUSHI-WETH', 'AAVE-WETH', 'UNI-USDC', 'UNI-WETH', 'LINK-WMATIC',
                    'WBTC-USDC1', 'LINK-USDC1', 'WMATIC-USDC', 'VOXEL-USDC', 'WETH-USDC', 'UNI-USDC']

    uniswap_v3_pools_100 = ['USDC-USDC1', 'USDC1-USDT', 'USDC1-DAI', 'USDC-USDT']
    sushiswap_v3_pools_100 = ['USDC-USDC1', 'USDC1-USDT', 'USDC1-DAI', 'USDC-USDT']
    converter = Converter('USDC', 100)
    slippage = 0.001
    uniswap_v3_100 = UniswapV3(network, subnet, api_key, 100, slippage=slippage)
    uniswap_v3_100.pair_list = uniswap_v3_pools_100

    uniswapv3_500 = UniswapV3(network, subnet, api_key, 500, slippage=slippage)
    uniswapv3_500.pair_list = uniswap_v3_pools_500

    uniswapv3_3000 = UniswapV3(network, subnet, api_key, 3000, slippage=slippage)
    uniswapv3_3000.pair_list = uniswap_v3_pools_3000

    sushi2 = SushiSwapV2(network, subnet, api_key, slippage=slippage)
    sushi2.pair_list = sushi2_pairs

    sushi3_100 = SushiSwapV3(network, subnet, api_key, 100, slippage=slippage)
    sushi3_100.pair_list = sushiswap_v3_pools_100

    sushi3_500 = SushiSwapV3(network, subnet, api_key, 500, slippage=slippage)
    sushi3_500.pair_list = sushi3_pools_500

    sushi3_3000 = SushiSwapV3(network, subnet, api_key, 3000, slippage=slippage)
    sushi3_3000.pair_list = sushi3_pools_3000

    trader = AdvancedTrader(uniswapv3_3000, uniswapv3_500, sushi2,
                            sushi3_3000, sushi3_500, uniswap_v3_100, sushi3_100, converter=converter, address=address,
                            private_key=private_key, thd=0.4)
    trader.arbitrage()

    # TODO: put pools with different comissions in one object, change exactInputSingle for exactOutputSingle, add more exchanges
    # print(get_contract(sushi3_100.web3_client,
    #                    abi_name="Uniswap-v3/Pool",
    #                    address="0x0e44cEb592AcFC5D3F09D996302eB4C499ff8c10",
    #                    net="Polygon", subnet="MAINNET").functions.slot0().call())
