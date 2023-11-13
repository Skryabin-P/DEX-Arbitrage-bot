import json
from web3 import Web3, AsyncWeb3
from DEX.utils import get_contract
from DEX.BaseToken import BaseToken
import os


class BaseExchange:
    _available_networks = None
    multicall_abi = 'ERC20/multicall'
    factory_abi = ''
    def __init__(self, network, subnet, api_key, fee=None):
        self.name = self.__class__.__name__
        self.network = network
        self.api_key = api_key
        self.subnet = subnet
        self._web3_provider = None
        self.web3_client = Web3(Web3.HTTPProvider(self.web3_provider))
        self.web3_client_async = AsyncWeb3(Web3.AsyncHTTPProvider(self.web3_provider))
        self.fee = fee
        self._price_book = None
        self._pair_list = None
        self._weth_addr = None
        self._multicall = None
        self._factory = None
        self._graph_endpoint = None

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
        if self._web3_provider is None:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'resources/web3_provider.json', 'r') as providers:
                providers = json.load(providers)
                self._web3_provider = providers[self.network][self.subnet] + self.api_key
        return self._web3_provider

    @property
    def fee(self):
        return self._fee

    @fee.setter
    def fee(self, fee: int):
        if fee is None:
            self._fee = 3000
        else:
            if not isinstance(fee, int):
                raise ValueError('Fee must be an integer')
            if fee < 0:
                raise ValueError('Fee can not be negative')
            self._fee = fee

    @property
    def price_book(self):
        return self._price_book

    @price_book.setter
    def price_book(self, price_book: dict):
        if not isinstance(price_book, dict):
            raise ValueError('Price book must be a dictionary!')
        self._price_book = price_book

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

    def get_token(self, symbol: str):

        with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'resources/tokens/{self.network}-{self.subnet.lower()}.json', 'r') as file:
            tokens = json.load(file)
            token = list(filter(lambda tokens: tokens['symbol'] == symbol.upper(), tokens))[0]
        return BaseToken(**token)



if __name__ == '__main__':
    from dotenv import load_dotenv
    import time
    from DEX.UniswapV2 import UniswapV2
    example = UniswapV2('Ethereum', 'MAINNET', 'sdadasd')

    a = example.get_token('WETH')
    print(a.name)

