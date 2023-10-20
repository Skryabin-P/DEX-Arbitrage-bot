import asyncio
import time

from BaseExchange import BaseExchange
from BaseToken import BaseToken
from utils import get_contract
import requests


class UniswapExchange(BaseExchange):
    def __init__(self, network, fee=None):
        super().__init__(network, fee)
        self._weth_addr = None
        self._pair_list = None
        self._price_book = None
        self._quoter = None
        self._quoter_async = None

    @property
    def quoter(self):
        if self._quoter is None:
            self._quoter = get_contract(self.web3_client, abi_name='Uniswap-v3/Quoter')
        return self._quoter

    @property
    def quoter_async(self):
        if self._quoter_async is None:
            self._quoter_async = get_contract(self.web3_client_async, abi_name='Uniswap-v3/Quoter')
        return self._quoter_async

    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.quoter.functions.WETH9().call()
        return self._weth_addr

    def _get_sell_price(self, base_asset: BaseToken, quote_asset: BaseToken, amount=1):
        converted_amount = amount * 10 ** base_asset.decimals
        sell_price = self.quoter_async.functions.quoteExactInputSingle(
            base_asset.address, quote_asset.address, self.fee, converted_amount, 0).call()
        return sell_price

    def _get_buy_price(self, base_asset: BaseToken, quote_asset: BaseToken, amount=1):
        converted_amount = amount * 10 ** base_asset.decimals
        buy_price = self.quoter.functions.quoteExactOutputSingle(
             quote_asset.address, base_asset.address, self.fee, converted_amount, 0).call()
        print(buy_price)
        return buy_price

    async def update_price_book(self, amount):
        print('Update price book')
        t1 = time.perf_counter()
        tasks = []
        pairs = []
        quotes = {}

        for pair, tokens in self.pair_list.items():
            base_asset = BaseToken(**tokens['base_asset'])
            quote_asset = BaseToken(**tokens['quote_asset'])
            buy_task = asyncio.create_task(self._get_buy_price(base_asset, quote_asset))
            sell_task = asyncio.create_task(self._get_sell_price(base_asset, quote_asset))
            tasks.append(buy_task)
            tasks.append(sell_task)
            pairs.append(pair)
        prices = await asyncio.gather(*tasks)

        for i in range(0, len(prices), 2):
            pair = pairs[i // 2]
            quotes[pair] = {'buy_price': prices[i],
                            'sell_price': prices[i + 1]}
        print(quotes)
        self._price_book = quotes
        t2 = time.perf_counter()
        print(f'It took {t2 - t1}s')

    def _fetch_top_volume_pools(self, pools_number: int):

        query = "{pools(first: %s, orderBy: volumeUSD, " \
                "orderDirection: desc where: {feeTier:%s})" \
                " {id " \
                "token0 {id name symbol decimals }" \
                "token1 { id name symbol decimals } } }" % (pools_number, self.fee)
        graph_endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
        response = requests.post(graph_endpoint, json={'query': query})
        return response.json()

    #
    @property
    def pair_list(self):
        print('Get pairlist')
        if self._pair_list is None:
            self._pair_list = {}
            top_pools = self._fetch_top_volume_pools(10)
            for pool in top_pools['data']['pools']:
                pair_name = f"{pool['token0']['symbol']}-{pool['token1']['symbol']}"
                address0 = self.web3_client.to_checksum_address(pool['token0']['id'])
                address1 = self.web3_client.to_checksum_address(pool['token1']['id'])
                if pair_name not in self._pair_list.keys():
                    token0 = {'name': pool['token0']['name'],
                              'address': address0,
                              'symbol': pool['token0']['symbol'],
                              'decimals': pool['token0']['decimals']}
                    token1 = {'name': pool['token1']['name'],
                              'address': address1,
                              'symbol': pool['token1']['symbol'],
                              'decimals': pool['token1']['decimals']}
                    self._pair_list[pair_name] = {'base_asset': token0, 'quote_asset': token1}
        return self._pair_list


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    import asyncio

    load_dotenv()
    network = os.environ['INFURA_MAINNET']
    Uniswap = UniswapExchange(network, fee=500)
    first_token = BaseToken(address='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', name='USDC',
                            symbol='USDC', decimals=6)
    second_token = BaseToken(address='0xa47c8bf37f92abed4a126bda807a7b7498661acd', name='UST',
                             symbol='UST', decimals=18)

    Uniswap._get_buy_price(first_token, second_token, 10)

    # TODO: Try to use multicall not async , drop async if it multicall is better
    #

