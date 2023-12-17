import time
from web3 import Web3
from eth_abi import encode
from DEX.UniswapV3 import UniswapV3
from DEX.UniswapV2 import UniswapV2
from DEX.SushiSwapV2 import SushiSwapV2
from DEX.SushiSwapV3 import SushiSwapV3
from DEX.PancakeSwapV3 import PancakeSwapV3
from DEX.PancakeSwapV2 import PancakeSwapV2
from DEX.Converter import Converter
from DEX.utils import get_contract
from Scanner import Scanner
import json
import codecs


class SimpleTrader:

    w3: Web3

    def __init__(self, *exchanges, converter, address, private_key, thd):
        self.exchanges = exchanges
        self.scanner = Scanner(self.exchanges, converter=converter)
        self.address = address
        self.private_key = private_key
        self.w3 = exchanges[0].web3_client
        self.thd = thd
        self.quote_amount = converter.quote_amount

    def arbitrage(self):
        while True:
            try:
                self.scanner.scan()
                arbitrage_table = json.loads(self.scanner.arbitrage_data)
                if arbitrage_table[1]['Profit %'] > self.thd:
                    print(f'Arbitrage opportunity found! \n {arbitrage_table[1]}')
                    for exchange in self.exchanges:
                        if exchange.name == arbitrage_table[1]['Exchange from']:
                            exchange_from = exchange
                        if exchange.name == arbitrage_table[1]['Exchange to']:
                            exchange_to = exchange
                    trade_from, amount_out, approve_from, token_from, flashloan_amount =\
                        self.encode_exchange_from(
                        arbitrage_table[1], exchange_from
                    )
                    trade_to, approve_to, token_to = self.encode_exchange_to(arbitrage_table[1],
                                                                             exchange_to, amount_out)
                    encoded_trades = [trade_from, trade_to]
                    encoded_approves = [approve_from, approve_to]
                    routers = [exchange_from.router.address,
                               exchange_to.router.address]
                    tokens = [token_from.address, token_to.address]
                    encoded_data = encode(types=['address[]', 'bytes[]', 'address[]', 'bytes[]'],
                                          args=[routers, encoded_trades, tokens, encoded_approves])

                    nonce = self.w3.eth.get_transaction_count(self.address)
                    chain_id = self.w3.eth.chain_id
                    gas_price = self.w3.eth.gas_price
                    min_income = (self.thd-0.2)/100 * self.quote_amount
                    if min_income > gas_price*700000 * 0.9 / 10**18 * 1.05:
                        request_flashloan = exchange_from.arbitrage_contract.functions.requestFlashLoan(
                            tokens[0], flashloan_amount,
                            encoded_data).build_transaction({"chainId": chain_id,
                                                             "from": self.address, "gas": 700000, "nonce": nonce,
                                                             'maxFeePerGas': int(gas_price * 1.05),
                                                             'maxPriorityFeePerGas': int(gas_price * 1)})
                        try:
                            signed_tx = self.w3.eth.account.sign_transaction(request_flashloan,
                                                                            private_key=self.private_key)

                            send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                            tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
                            print(tx_receipt)
                            time.sleep(1)
                            continue
                        except Exception as e:
                            print(e)
                    else:
                        print('Potential income do not worth transaction fee')
                time.sleep(10)
            except:
                time.sleep(10)
                continue


    def encode_exchange_from(self, arbitrage_line, exchange_from):
        pair = arbitrage_line['Pair']
        buy_price = arbitrage_line['Buy price']
        buy_amount = arbitrage_line['buy amount']
        base_asset = exchange_from.pair_list[pair]['base_asset']
        quote_asset = exchange_from.pair_list[pair]['quote_asset']
        amount_in = buy_price * buy_amount
        buy_order, amount_out = exchange_from.encode_buy_order(base_asset,
                                                               quote_asset, amount_in, buy_amount)
        approve = exchange_from.encode_router_approve(quote_asset, amount_in)
        approve = codecs.decode(approve[2:], 'hex_codec')
        buy_order = codecs.decode(buy_order[2:], 'hex_codec')
        flashloan_amount = int(amount_in * 10**base_asset.decimals)
        return buy_order, amount_out, approve, quote_asset, flashloan_amount

    def encode_exchange_to(self, arbitrage_line, exchange_to, amount_in):
        pair = arbitrage_line['Pair']
        sell_price = arbitrage_line['Sell price']
        amount_out = sell_price * amount_in
        base_asset = exchange_to.pair_list[pair]['base_asset']
        quote_asset = exchange_to.pair_list[pair]['quote_asset']
        buy_order, _ = exchange_to.encode_buy_order(quote_asset,
                                                    base_asset, amount_in, amount_out)
        buy_order = codecs.decode(buy_order[2:], 'hex_codec')
        approve = exchange_to.encode_router_approve(base_asset, amount_in)
        approve = codecs.decode(approve[2:], 'hex_codec')
        return buy_order, approve, base_asset


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
    uniswap_v3_pools_3000 = ['WMATIC-WETH', 'WBTC-USDC', 'LINK-USDC',
                             'LINK-WETH', 'WBTC-WETH', 'WMATIC-USDC', 'AAVE-WETH',
                             'VOXEL-USDC', 'WETH-USDC', 'WETH-USDT', 'UNI-WETH']
    uniswap_v3_pools_500 = ['WETH-USDC', 'WBTC-WETH', 'WMATIC-USDC', 'WMATIC-WETH', 'WMATIC-USDC',
                            'WMATIC-USDT', 'WETH-USDC', 'WBTC-USDC', 'PAR-USDC']

    sushi3_pools_3000 = ['WETH-USDC', 'WBTC-USDC', 'SUSHI-WETH', 'WETH-USDT', 'MANA-WETH',
                         'WBTC-WETH', 'STG-USDC', 'AVAX-WETH', 'WMATIC-USDC', 'WMATIC-WETH',
                         'WMATIC-USDT', 'AAVE-WETH', 'WMATIC-DAI', 'WETH-DAI', 'BAL-USDC',
                         'MVI-USDT', 'SUSHI-USDC', 'CRV-WETH']
    sushi3_pools_500 = ['WMATIC-USDC', 'WMATIC-WETH', 'CGG-WETH', 'WETH-USDC', 'WMATIC-USDT',
                        'WMATIC-DAI', 'WBTC-USDT', 'WETH-DAI']

    sushi2_pairs = ['WMATIC-WETH', 'STG-USDC', 'NCT-USDC', 'KLIMA-USDC', 'WETH-USDC',
                    'WBTC-WETH', 'WETH-DAI', 'AAVE-WETH', 'WMATIC-USDC', 'LINK-WETH', 'WETH-USDT',
                    'AVAX-WETH', 'MANA-WETH', 'CRV-WETH', 'UNI-WETH', 'BAL-WETH',
                    'SUSHI-WETH', 'AAVE-WETH', 'UNI-USDC', 'UNI-WETH']


    converter = Converter('USDC', 100)

    uniswapv3_500 = UniswapV3(network, subnet, api_key, 500, slippage=0.1)
    uniswapv3_500.pair_list = uniswap_v3_pools_500

    uniswapv3_3000 = UniswapV3(network, subnet, api_key, 3000, slippage=0.1)
    uniswapv3_3000.pair_list = uniswap_v3_pools_3000

    sushi2 = SushiSwapV2(network, subnet, api_key, slippage=0.1)
    sushi2.pair_list = sushi2_pairs

    sushi3_500 = SushiSwapV3(network, subnet, api_key, 500, slippage=0.1)
    sushi3_500.pair_list = sushi3_pools_500

    sushi3_3000 = SushiSwapV3(network, subnet, api_key, 3000, slippage=0.1)
    sushi3_3000.pair_list = sushi3_pools_3000

    trader = SimpleTrader(uniswapv3_3000, uniswapv3_500, sushi2,
                          sushi3_3000, sushi3_500, converter=converter, address=address,
                          private_key=private_key, thd=0.6)
    trader.arbitrage()
