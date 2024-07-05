import time
from web3 import Web3
from eth_abi import encode
from DEX.UniswapV3 import UniswapV3
from DEX.SushiSwapV2 import SushiSwapV2
from DEX.SushiSwapV3 import SushiSwapV3
from DEX.Converter import Converter
from DEX.utils import get_contract
from AdvancedScanner import AdvancedScanner
from threading import Thread
import codecs
from operator import itemgetter


class AdvancedTrader:
    w3: Web3

    def __init__(self, *exchanges, quote_asset, quote_amount,
                 address, private_key, thd, slippage):
        self.exchanges = {exchange.name: exchange for exchange in exchanges}
        self.scanner = AdvancedScanner(*exchanges, quote_asset=quote_asset, quote_amount=quote_amount)
        self.converter = Converter(quote_asset, quote_amount)
        self.converter.convert()
        self.address = address
        self.private_key = private_key
        self.w3 = exchanges[0].web3_client
        self.thd = thd
        self.slippage = slippage
        self.quote_amount = self.converter.quote_amount
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
                        # Loop through the arbitrage steps and collect all needed data for my smart contract
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
                        # If potential income more than gas fees
                        request_flashloan = self.arbitrage_contract.functions.requestFlashLoan(
                            tokens[0], flashloan_amount,
                            encoded_data).build_transaction({"chainId": self.chain_id,
                                                             "from": self.address, "gas": gas, "nonce": self.nonce,
                                                             'maxFeePerGas': int(self.gas_price * 1.05),
                                                             'maxPriorityFeePerGas': int(self.gas_price * 1)})
                        try:
                            signed_tx = self.w3.eth.account.sign_transaction(request_flashloan,
                                                                             private_key=self.private_key)

                            send_tx = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                            tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
                            print(tx_receipt)
                            time.sleep(1)
                            break

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
        """
        Encode order and approve function
        @param step: arbitrage step
        @param prices: quotes for this step
        @param amount_in:
        @return: returns encoded order, approve, amount_out_min,
        quote asset in this trade and router address
        """
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
            base_asset, quote_asset, amount_in, amount_out, self.arbitrage_contract.address, self.slippage)
        approve = exchange.encode_router_approval(quote_asset, amount_in)
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
        # get actual nonce, gas price and chain id
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
    net = "Polygon"
    subnet = "MAINNET"
    web3_provider = os.environ['INFURA_POLYGON']
    private_key = os.environ['PRIVATE_KEY']
    address = os.environ['WALLET_ADDRESS']
    parse_net = 'polygon_pos'

    from PoolsParser.Parser import PoolsParser

    uniswap_v3_parser = PoolsParser(parse_net, 'uniswap_v3_polygon_pos', pg_number=7)
    sushi3_parser = PoolsParser(parse_net, 'sushiswap-v3-polygon', pg_number=7)
    sushi2_parser = PoolsParser(parse_net, 'sushiswap_polygon_pos', pg_number=7)

    uniswapV3_10000 = UniswapV3(net, subnet, web3_provider, fee=10000)
    uniswapV3_10000.add_pools(uniswap_v3_parser.top_pools[10000])
    uniswapV3_3000 = UniswapV3(net, subnet, web3_provider, 3000)
    uniswapV3_3000.add_pools(uniswap_v3_parser.top_pools[3000])
    uniswapV3_500 = UniswapV3(net, subnet, web3_provider, 500, )
    uniswapV3_500.add_pools(uniswap_v3_parser.top_pools[500])
    uniswapV3_100 = UniswapV3(net, subnet, web3_provider, 100, )
    uniswapV3_100.add_pools(uniswap_v3_parser.top_pools[100])
    sushi3_10000 = SushiSwapV3(net, subnet, web3_provider, 10000)
    sushi3_10000.add_pools(sushi3_parser.top_pools[10000])
    sushi3_3000 = SushiSwapV3(net, subnet, web3_provider, 3000, )
    sushi3_3000.add_pools(sushi3_parser.top_pools[3000])

    sushi3_500 = SushiSwapV3(net, subnet, web3_provider, 500, )
    sushi3_500.add_pools(sushi3_parser.top_pools[500])

    sushi3_100 = SushiSwapV3(net, subnet, web3_provider, 100, )
    s3_100 = sushi3_parser.top_pools[100]
    sushi3_100.add_pools(s3_100)
    sushi2 = SushiSwapV2(net, subnet, web3_provider, )
    sushi2.add_pools(sushi2_parser.top_pools[3000])

    slippage = 0.001

    trader = AdvancedTrader(uniswapV3_10000, uniswapV3_3000, uniswapV3_500, uniswapV3_100, sushi2,
                            sushi3_10000, sushi3_3000, sushi3_500, sushi3_100, quote_asset='USDC',
                            quote_amount=10, address=address,
                            private_key=private_key, thd=0.2, slippage=slippage)
    trader.arbitrage()
