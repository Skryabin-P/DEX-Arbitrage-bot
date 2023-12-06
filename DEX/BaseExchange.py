import json
from web3 import Web3, AsyncWeb3
from DEX.utils import get_contract
from DEX.BaseToken import BaseToken
import os


class BaseExchange:
    _available_networks = None
    multicall_abi = 'ERC20/multicall'
    factory_abi = ''
    _quote_asset_prices = None

    def __init__(self, network, subnet, api_key=None, web3_provider=None):
        self._price_book = None
        self._pair_list = None
        self._weth_addr = None
        self._multicall = None
        self._factory = None
        self._graph_endpoint = None
        self._web3_provider = None

        self.name = self.__class__.__name__
        self.network = network
        self.api_key = api_key
        self.subnet = subnet
        self.web3_provider = web3_provider
        self.web3_client = Web3(Web3.HTTPProvider(self.web3_provider, request_kwargs={'timeout': 600}))
        self.web3_client_async = AsyncWeb3(Web3.AsyncHTTPProvider(self.web3_provider))


    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, network):
        if network not in self.available_networks:
            available_networks = ",".join(self.available_networks)
            raise ValueError(f"Network must be {available_networks}"
                             f"\ngot {network} instead")
        self._network = network

    @property
    def subnet(self):
        return self._subnet

    @subnet.setter
    def subnet(self, subnet):
        available_subnets = ['MAINNET', 'TESTNET']
        if subnet not in available_subnets:
            raise ValueError(f"Subnet must be {str(',').join(available_subnets)}"
                             f" got {subnet} instead")
        self._subnet = subnet

    @property
    def web3_provider(self):
        return self._web3_provider

    @web3_provider.setter
    def web3_provider(self, provider):
        if provider is None:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'resources/web3_provider.json', 'r') as providers:
                providers = json.load(providers)
                self._web3_provider = providers[self.network][self.subnet] + self.api_key
        else:
            self._web3_provider = provider



    @property
    def price_book(self):
        return self._price_book

    @price_book.setter
    def price_book(self, price_book: dict):
        if not isinstance(price_book, dict):
            raise ValueError('Price book must be a dictionary!')
        self._price_book = price_book

    @property
    def quote_asset_prices(self):
        # if self._quote_asset_prices is None:
        #     raise ValueError('quote_asset_prices must be set! Use set_quote_asset_prices method')
        return BaseExchange._quote_asset_prices

    @quote_asset_prices.setter
    def quote_asset_prices(self, prices: dict):
        if not isinstance(prices, dict):
            raise ValueError('quote_asset_prices must be a dictionary!')
        BaseExchange._quote_asset_prices = prices

    @property
    def graph_endpoint(self):
        if self._graph_endpoint is None:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'resources/graph_endpoint.json', 'r') as file:
                self._graph_endpoint = json.load(file)[self.name][self.network]
        return self._graph_endpoint

    @property
    def available_networks(self):
        if self._available_networks is None:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'resources/graph_endpoint.json', 'r') as file:
                self._available_networks = json.load(file)[self.name].keys()
        return self._available_networks

    @property
    def multicall(self):
        if self._multicall is None:
            self._multicall = get_contract(self.web3_client, abi_name=self.multicall_abi,
                                           net=self.network, subnet=self.subnet)
        return self._multicall

    @property
    def factory(self):
        if self._factory is None:
            self._factory = get_contract(self.web3_client, self.factory_abi,
                                         self.network, self.subnet)
        return self._factory

    @property
    def pair_list(self):
        return self._pair_list

    @pair_list.setter
    def pair_list(self, pairs: list[str]):
        self._pair_list = {}
        if not isinstance(pairs, list):
            raise ValueError(f'pair_list must be a list of trading pairs got {type(pairs)} instead')
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                  f'resources/tokens/{self.network}-{self.subnet.lower()}.json', 'r') as file:
            tokens = json.load(file)
        for pair in pairs:
            if not isinstance(pair, str):
                raise ValueError(f'Each pair must be a string, got {pair} instead')
            if '-' not in pair:
                raise ValueError(f'Pair must follow a pattern "coin1-coin2" with "-" delimiter ')

            symbol1 = pair.split('-')[0].upper()
            symbol2 = pair.split('-')[1].upper()
            search_result_symbol1 = list(filter(lambda token: token['symbol'] == symbol1.upper(), tokens))
            search_result_symbol2 = list(filter(lambda token: token['symbol'] == symbol2.upper(), tokens))
            if len(search_result_symbol1) < 1:
                raise ValueError(f"Couldn't find symbol {symbol1}")
            if len(search_result_symbol2) < 1:
                raise ValueError(f"Couldn't find symbol {symbol2}")
            token1 = BaseToken(**search_result_symbol1[0])
            token2 = BaseToken(**search_result_symbol2[0])
            self._pair_list[pair] = {'base_asset': token1, 'quote_asset': token2}

    def convert_from_universal_amount(self, currency):
        pass


if __name__ == '__main__':
    from dotenv import load_dotenv
    import time
    from DEX.UniswapV2 import UniswapV2
    from DEX.UniswapV3 import UniswapV3
    from DEX.Converter import Converter
    load_dotenv()
    pairs = ['WETH-usdc', 'aave-weth']
    infura_api_key = os.environ['INFURA_API_KEY']
    converter = Converter('USDC', 1000)
    example2 = UniswapV3('Ethereum', 'MAINNET', infura_api_key, fee=3000)
    example2.multicall_abi = 'ERC20/multicall'
    example2.pair_list = pairs
    example1 = UniswapV2('Ethereum', 'MAINNET', infura_api_key)
    example1.pair_list = pairs
    example2.quote_asset_prices = converter.convert()
    print(example1.quote_asset_prices)
    print(example2.quote_asset_prices)
    print(example1.quote_asset_prices)
    example1.update_price_book()
    example2.update_price_book()
    print(example1.price_book)
    print(example2.price_book)
    # example2.update_price_book()
    # print(example2.price_book)
    # TODO: I need some method or converter class to convert universal asset to quote asset
