import asyncio
from .BaseExchange import BaseExchange
from .BaseToken import BaseToken
from .utils import get_contract
import requests


class UniswapExchange(BaseExchange):
    def __init__(self, network, fee=None):
        super().__init__(network, fee)
        self._weth_addr = None
        self._pair_list = None

    @property
    def quoter(self):
        return get_contract(self.web3_client, abi_name='Uniswap-v3/Quoter')

    @property
    def quoter_async(self):
        return get_contract(self.web3_client_async, abi_name='Uniswap-v3/Quoter')

    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.quoter.functions.WETH9().call()
        return self._weth_addr

    def _get_sell_price(self, base_asset: BaseToken, quote_asset: BaseToken, amount: int):
        converted_amount = amount * 10 ** base_asset.decimals
        sell_price = self.quoter.functions.quoteExactInputSingle(
            base_asset.address, quote_asset.address, self.fee, converted_amount, 0).call() / amount
        return sell_price / 10 ** quote_asset.decimals

    def _get_buy_price(self, base_asset: BaseToken, quote_asset: BaseToken, amount):
        converted_amount = amount * 10 ** base_asset.decimals
        buy_price = self.quoter.functions.quoteExactOutputSingle(
            quote_asset.address, base_asset.address, self.fee, converted_amount, 0).call() / amount
        return buy_price / 10 ** quote_asset.decimals

    @staticmethod
    def _fetch_top_volume_pools(pools_number: int):
        query = "{pools(first: %s, orderBy: volumeUSD, orderDirection: desc)" \
                " {id " \
                "token0 {id name symbol decimals }" \
                "token1 { id name symbol decimals } } }" % pools_number
        graph_endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
        response = requests.post(graph_endpoint, json={'query': query})
        return response.json()

    @property
    def pair_list(self):
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
        return self._pair_list


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    import asyncio
    load_dotenv()
    network = os.environ['INFURA_MAINNET']
    Uniswap = UniswapExchange(network)
    weth = BaseToken(address=Uniswap.weth_addr, name='WETH', symbol='WETH', decimals=18)
    usdt_token = BaseToken(address='0xdAC17F958D2ee523a2206206994597C13D831ec7', name='Tether',
                           symbol='USDT', decimals=6)




    for pair in Uniswap.pair_list:
        token0 = BaseToken(**Uniswap.pair_list[pair]['base_asset'])
        token1 = BaseToken(**Uniswap.pair_list[pair]['quote_asset'])
        sell_price = Uniswap._get_sell_price(token0, token1, 10)
        buy_price = Uniswap._get_buy_price(token0, token1, 10)
        print(f'{pair} {buy_price} {sell_price}')

    # sell_price = Uniswap._get_sell_price(weth, usdt_token, 1)
    # print(sell_price)
    # buy_price = Uniswap._get_buy_price(weth, usdt_token, 1)
    # print(buy_price)
    #
    # Uniswap.get_token('0x514910771AF9Ca656af840dff83E8264EcF986CA')