import json
from web3 import Web3, AsyncWeb3
from DEX.utils import get_contract
from DEX.BaseToken import BaseToken
import os
from urllib.parse import urlparse
import time


class BaseExchange:
    _available_networks = None
    multicall_abi = 'General/multicall'
    factory_abi = ''
    _quote_asset_prices = None
    router_abi = ''

    def __init__(self, network, subnet, web3_provider=None):
        self._pair_list = None
        self._weth_addr = None
        self._multicall = None
        self._factory = None
        self._router = None
        self._arbitrage_contract = None
        self._price_book = None

        self.name = self.__class__.__name__
        self.network = network
        self.subnet = subnet
        self.web3_provider = web3_provider
        self.web3_client = Web3(Web3.HTTPProvider(self.web3_provider, request_kwargs={'timeout': 600}))
        self.web3_client_async = AsyncWeb3(Web3.AsyncHTTPProvider(self.web3_provider))

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, network):
        if network.upper() not in self.available_networks:
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
    def web3_provider(self, provider: str):
        # Just an HTTP/HTTPS RPC node url
        if not isinstance(provider, str):
            raise ValueError("Web3 provider must be an http/https url string")
        provider = provider.lower()
        parsed_web3_url = urlparse(provider)
        if not parsed_web3_url.scheme or not parsed_web3_url.netloc:
            raise ValueError("Not valid web3 provider url was given")
        if parsed_web3_url.scheme not in ['http', 'https']:
            raise ValueError(f"Web3 provider url must be http or https but {parsed_web3_url.scheme} was given")
        self._web3_provider = provider

    @property
    def price_book(self):
        # Property which contains quotes from DEX for pairs in pair_list property
        return self._price_book

    @price_book.setter
    def price_book(self, price_book: dict):
        if not isinstance(price_book, dict):
            raise ValueError('Price book must be a dictionary!')
        self._price_book = price_book

    @property
    def quote_asset_prices(self):
        # Exchange rate between quote asset USDC, USDT, ETH and DAI
        return BaseExchange._quote_asset_prices

    @quote_asset_prices.setter
    def quote_asset_prices(self, prices: dict):
        if not isinstance(prices, dict):
            raise ValueError('quote_asset_prices must be a dictionary!')
        BaseExchange._quote_asset_prices = prices

    @property
    def available_networks(self):
        """
        There's contract_address.json In the Abi folder of each exchange
        that contains addresses for different networks of some DEX contracts
        like Quoter, SwapRouter, Factory. That property get networks
        for a contract Factory in this file
        @return: set of available networks
        """
        if self._available_networks is None:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'ABI/{self.__class__.__name__}/contract_addresses.json', 'r') as file:
                self._available_networks = json.load(file)["Factory"].keys()
        return self._available_networks

    @property
    def multicall(self):
        # multicall contract instance
        if self._multicall is None:
            self._multicall = get_contract(self.web3_client, abi_name=self.multicall_abi,
                                           net=self.network, subnet=self.subnet)
        return self._multicall

    @property
    def router(self):
        # router V2 or V3 contract instance
        if self._router is None:
            self._router = get_contract(self.web3_client, abi_name=self.router_abi,
                                        net=self.network, subnet=self.subnet)
        return self._router


    @property
    def factory(self):
        # Factory contract instance
        if self._factory is None:
            self._factory = get_contract(self.web3_client, self.factory_abi,
                                         self.network, self.subnet)
        return self._factory

    @property
    def pair_list(self) -> dict:
        return self._pair_list

    @pair_list.setter
    def pair_list(self, pairs: list[str]):
        """
        @param pairs: list of trading pairs in format token0-token1, with "-" delimiter between tokens
        """
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
            search_result_symbol1 = list(filter(lambda token: token['symbol'].upper() == symbol1, tokens))
            search_result_symbol2 = list(filter(lambda token: token['symbol'].upper() == symbol2, tokens))
            if len(search_result_symbol1) < 1:
                raise ValueError(f"Couldn't find symbol {symbol1}, \n"
                                 f"Try to add manually using add_pair method")
            if len(search_result_symbol2) < 1:
                raise ValueError(f"Couldn't find symbol {symbol2}, \n"
                                 f"Try to add manually using add_pair method")
            token1 = BaseToken(**search_result_symbol1[0])
            token2 = BaseToken(**search_result_symbol2[0])
            self._pair_list[pair] = {'base_asset': token1, 'quote_asset': token2}

    def encode_router_approve(self, token: BaseToken, amount):
        """
        @param token: BaseToken object
        @param amount: human-readable amount of token
        @return: encoded approve function for exchange router with parameters
        """
        converted_amount = int(amount * 10 ** token.decimals)
        return get_contract(self.web3_client, 'General/erc20', self.network,
                            self.subnet, token.address).encodeABI(fn_name='approve',
                                                                  args=(self.router.address,
                                                                        converted_amount))

    @staticmethod
    def _deadline():
        return int(time.time()) + 60


if __name__ == '__main__':
    from dotenv import load_dotenv
    from DEX.UniswapV2 import UniswapV2
    from DEX.UniswapV3 import UniswapV3
    from DEX.PancakeSwapV3 import PancakeSwapV3
    from DEX.Converter import Converter

    load_dotenv()
    pairs = ['WETH-usdc', 'aave-weth']
    infura_api_key = os.environ['INFURA_API_KEY']
    # converter = Converter('USDC', 1000)
    exchange = PancakeSwapV3('Ethereum', 'MAINNET', web3_provider='HTTP://127.0.0.1:7545', fee=500, slippage=0.2)
    print(exchange.available_networks)

