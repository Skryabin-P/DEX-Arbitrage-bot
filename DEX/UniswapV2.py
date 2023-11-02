import time
from web3._utils.abi import get_abi_output_types
from .BaseExchange import BaseExchange
from .BaseToken import BaseToken
from .utils import get_contract, exec_time, get_function_abi
import requests


class UniswapV2(BaseExchange):
    router_abi = 'Uniswap-v2/Router02'
    graph_endpoint = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v2-dev"

    def __init__(self, network, fee=None, num_pairs: int = 10):
        super().__init__(network, fee)
        self.num_pairs = num_pairs
        self.name = self.__class__.__name__
        self._router = None
        self._multicall = None
        self._router_calls = None
        self._router_output_types = None

    @property
    def router(self):
        if self._router is None:
            self._router = get_contract(self.web3_client, abi_name=self.router_abi)
        return self._router

    @property
    def multicall(self):
        if self._multicall is None:
            self._multicall = get_contract(self.web3_client, abi_name='ERC20/multicall')
        return self._multicall

    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.router.functions.WETH().call()
        return self._weth_addr

    def _encode_sell_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: float = 1):
        """
        returns encoded  sell function for pushing to milticall contract
        """
        converted_amount = amount * 10 ** base_asset.decimals
        route = [base_asset.address, quote_asset.address, ]
        return self.router.encodeABI(fn_name='getAmountsOut',
                                     args=(converted_amount, route))

    def _encode_buy_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: float = 1):
        """
        returns encoded  buy function for pushing to milticall contract
        """
        converted_amount = amount * 10 ** base_asset.decimals
        route = [quote_asset.address, base_asset.address]
        # print(self.router.functions.getAmountsIn(converted_amount, route).call()[0] / 10 ** quote_asset.decimals)
        return self.router.encodeABI(fn_name='getAmountsIn',
                                     args=(converted_amount, route))

    @property
    def router_calls(self) -> list[tuple]:
        # amount means amount of coins
        if self._router_calls is None:
            self._router_calls = []
            for tokens in self.pair_list.values():
                base_asset = tokens['base_asset']
                quote_asset = tokens['quote_asset']
                buy_call = self._encode_buy_price_func(base_asset, quote_asset, 1)
                sell_call = self._encode_sell_price_func(base_asset, quote_asset, 1)
                self._router_calls.append((self.router.address, buy_call))
                self._router_calls.append((self.router.address, sell_call))
        return self._router_calls

    @property
    def router_output_types(self) -> list[str]:
        """
        I decided to use getAmountsIn for getting types,
        because it has the same types as getAmountsOut

        return: list of string representation of types for decoding
        after multicall
        """
        if self._router_output_types is None:
            abi_function = get_function_abi(abi_name=self.router_abi,
                                            func_name='getAmountsIn')
            self._router_output_types = get_abi_output_types(abi_function)
        return self._router_output_types

    def _fetch_top_volume_pairs(self):

        query = "{pairs(first: %s, orderBy: reserveUSD  orderDirection: desc)" \
                " {id " \
                "token0 {id name symbol decimals }" \
                "token1 { id name symbol decimals } } }" % self.num_pairs
        # dev cause it works, official doesn't sync at all

        response = requests.post(self.graph_endpoint, json={'query': query})
        return response.json()

    def decode_multicall_router(self, multicall_raw_data):
        quotes = {}
        for i in range(0, len(multicall_raw_data), 2):
            pair = list(self.pair_list.keys())[i // 2]  # just pair name

            buy_price = None
            sell_price = None
            buy_call_success = multicall_raw_data[i][0]
            sell_call_success = multicall_raw_data[i+1][0]
            quote_asset_decimals = self.pair_list[pair]['quote_asset'].decimals
            if buy_call_success:
                buy_price = self.web3_client.codec.decode(
                    self.router_output_types,
                    multicall_raw_data[i][1])[0][0] / 10 ** quote_asset_decimals
            if sell_call_success:
                sell_price = self.web3_client.codec.decode(
                    self.router_output_types,
                    multicall_raw_data[i + 1][1])[0][1] / 10 ** quote_asset_decimals

            quotes[pair] = {'buy_price': buy_price,
                            'sell_price': sell_price}
        return quotes


    def update_price_book(self):

        print('Update price book')

        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, self.router_calls).call()

        self.price_book = self.decode_multicall_router(multicall_raw_data)

    @property
    def pair_list(self):
        if self._pair_list is None:
            print(f"Getting pairlist for {self.name}")
            self._pair_list = {}
            top_pairs = self._fetch_top_volume_pairs()
            for pair in top_pairs['data']['pairs']:
                pair_name = f"{pair['token0']['symbol']}-{pair['token1']['symbol']}"
                if pair_name not in self._pair_list.keys():
                    token0 = BaseToken(name=pair['token0']['name'],
                                       address=pair['token0']['id'],
                                       symbol=pair['token0']['symbol'],
                                       decimals=pair['token0']['decimals'])
                    token1 = BaseToken(name=pair['token1']['name'],
                                       address=pair['token1']['id'],
                                       symbol=pair['token1']['symbol'],
                                       decimals=pair['token1']['decimals'])
                    self._pair_list[pair_name] = {'base_asset': token0, 'quote_asset': token1}
        return self._pair_list


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
    client = UniswapV2(net)

    print(client.pair_list['not_in_list'])
    # client.update_price_book(1)
    # print(client.price_book)
    # time.sleep(1)
    # client.update_price_book(1)
    # print(client.price_book)
    # client.update_price_book(1)
    # print(client.price_book)
    # base_asset = BaseToken(name="WETH", address=client.weth_addr, decimals=18)
    # quote_asset = BaseToken(name="USDT", address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    #                         decimals=6)
    #
    # client._encode_sell_price_func(base_asset, quote_asset)
    # client._encode_buy_price_func(base_asset, quote_asset)
