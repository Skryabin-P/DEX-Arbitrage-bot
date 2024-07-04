import json
from typing import Any

from web3 import Web3, AsyncWeb3
from web3.contract.contract import ContractFunction
from DEX.utils import get_contract
from DEX.Token import Token
from DEX.constants import AVAILABLE_SUBNETS
import os
from urllib.parse import urlparse
import time


class BaseExchange:
    """
    The parent class for other Exchange classes
    Contains main properties and methods
    """

    # The same for all child classes
    _quote_asset_prices = None

    def __init__(self, network, subnet, web3_provider=None, pairs=None):
        """
        @param network: Network name like "Ethereum", "Polygon", etc.
        All available networks in available_networks property
        @param subnet: MAINNET or TESTNET
        @param web3_provider: HTTP or HTTPS url for connecting to RPC node
        @param pairs: List of pairs in format "Token0-Token1"
        """
        self._pair_list = None
        self._weth_addr = None
        self._multicall = None
        self._factory = None
        self._router = None
        self._price_book = None
        self._available_networks = None
        self.multicall_abi = 'General/multicall'
        self.factory_abi = ''
        self.router_abi = ''

        self.name = self.__class__.__name__
        self.network = network
        self.subnet = subnet
        self.web3_provider = web3_provider
        self.web3_client = Web3(Web3.HTTPProvider(self.web3_provider))
        self.web3_client_async = AsyncWeb3(Web3.AsyncHTTPProvider(self.web3_provider))
        if pairs is not None:
            self.pair_list = pairs

    @property
    def network(self):
        """
        @return: Network name like Ethereum, Arbitrub, etc
        """
        return self._network

    @network.setter
    def network(self, network):
        """
        Set the network property
        @param network: name of the network like Ethereum, Arbitrub, Polygon
        @raise ValueError: If passed network is not in available_networks
        """
        if network.upper() not in self.available_networks:
            available_networks = ",".join(self.available_networks)
            raise ValueError(f"Network must be {available_networks}"
                             f"\ngot {network} instead")
        self._network = network

    @property
    def subnet(self):
        """ MAINNET or TESTNET """
        return self._subnet

    @subnet.setter
    def subnet(self, subnet):
        """
        Set the subnet property
        @param subnet: name of the subnet, may be MAINNET or TESTNET
        @raise ValueError: If passed subnet not MAINNET or TESTNET
        """
        if subnet not in AVAILABLE_SUBNETS:
            raise ValueError(f"Subnet must be {','.join(AVAILABLE_SUBNETS)}"
                             f" got {subnet} instead")
        self._subnet = subnet

    @property
    def web3_provider(self):
        # HTTP/HTTPS url blockhain rpc provider
        return self._web3_provider

    @web3_provider.setter
    def web3_provider(self, provider: str):
        """
        Set the web3_provider property
        @param provider: an HTTP/HTTPS url blockhain rpc provider
        @raise ValueError: If provider is not correct http/https url string
        """
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
    def price_book(self) -> dict:
        """
        Property which contains quotes from DEX for pairs in {pair_list} property
        """
        return self._price_book

    @price_book.setter
    def price_book(self, price_book: dict):
        """
        Set the price_book property
        @param price_book: A dictionary which contains prices
        @raise ValueError: If passed price_book is not a dictionary
        """
        if not isinstance(price_book, dict):
            raise ValueError('Price book must be a dictionary!')
        self._price_book = price_book

    @property
    def quote_asset_prices(self):
        """Exchange rate between quote asset USDC, USDT, ETH , DAI and WMATIC"""
        return BaseExchange._quote_asset_prices

    @quote_asset_prices.setter
    def quote_asset_prices(self, prices: dict):
        """
        Set quote_asset_prices property for every Exchange class
        @param prices: a dictionary which contains prices for quote assets
        @raise ValueError: If passed prices is not dictionary
        """
        if not isinstance(prices, dict):
            raise ValueError('quote_asset_prices must be a dictionary!')
        BaseExchange._quote_asset_prices = prices

    @property
    def available_networks(self):
        """
        Every exchange class has own ABI folder containing contract addresses file
        for all available networks DEX/ABI/{ExchangeName}/contract_addresses.json
        That property gets available networks from this file for a Factory contract
        @return: set of available networks
        """
        if self._available_networks is None:
            with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
                      f'ABI/{self.__class__.__name__}/contract_addresses.json', 'r') as file:
                self._available_networks = json.load(file)["Factory"].keys()
        return self._available_networks

    @property
    def multicall(self):
        """
        Multicall is a special smart contract which can do
        multiple read blockchain operations at once
        @return: multicall contract instance
        """
        if self._multicall is None:
            self._multicall = get_contract(self.web3_client, abi_name=self.multicall_abi,
                                           net=self.network, subnet=self.subnet)
        return self._multicall

    @property
    def router(self):
        """
        Router or SwapRouter is a contract that is commonly used for trading purposes
        @return: router contract instance for V2 or V3 exchange
        """
        if self._router is None:
            self._router = get_contract(self.web3_client, abi_name=self.router_abi,
                                        net=self.network, subnet=self.subnet)
        return self._router

    @property
    def factory(self):
        """
        Factory is a contract that is commonly used for creation Pools or Pairs
        @return: factory contract instance
        """
        if self._factory is None:
            self._factory = get_contract(self.web3_client, self.factory_abi,
                                         self.network, self.subnet)
        return self._factory

    @property
    def pair_list(self) -> dict:
        # Dictionary for pairs containing base and quote assets Token objects
        return self._pair_list

    @pair_list.setter
    def pair_list(self, pairs: list[str]):
        """
        For a given pair finds tokens in DEX/resources/tokens/{current-network}.json
        This token information was webscraped from different Exchange.
        You can add tokens to this json files if you need. or with add_pair method
        Creates Token objects for each token in pair and add them to a ditctionary
        @param pairs: list of trading pairs in format "token0_name-token1_name", with "-" delimiter between tokens
        @raise ValueError:
            1. If passed pairs parameter is not a list
            2. If pair in pairs list is not a string
            3. If one or both tokens are not found
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
            token0 = Token(**search_result_symbol1[0])
            token1 = Token(**search_result_symbol2[0])
            self._pair_list[pair] = {'base_asset': token0, 'quote_asset': token1}

    def encode_router_approval(self, token: Token, amount):
        """
        Encode ERC20 approve function for Router or SwapRouter contract
        @param token: Token object
        @param amount: human-readable amount of token, how many to approve
        @return: encoded approve ERC20 function for exchange router with parameters
        """
        converted_amount = int(amount * 10 ** token.decimals)
        return get_contract(self.web3_client, 'General/erc20', self.network,
                            self.subnet, token.address).encodeABI(fn_name='approve',
                                                                  args=(self.router.address,
                                                                        converted_amount))

    def add_pair(self, token0: Token, token1: Token):
        """
        Add pair to pair_list property
        @param token0: Token obj of token0
        @param token1: Token obj of token1
        @raise ValueError: If token0 or token1 is not Token objects
        """

        if not isinstance(token0, Token) or not isinstance(token1, Token):
            raise ValueError("token 0 and token1 must be the Token class instances!")

        if self._pair_list is None:

            self._pair_list = {f"{token0.symbol.upper()}-{token1.symbol.upper()}":
                                  {'base_asset': token0, 'quote_asset': token1}}
        else:
            self._pair_list[f"{token0.symbol.upper()}-{token1.symbol.upper()}"] = \
                {'base_asset': token0, 'quote_asset': token1}

    def add_pools(self, pools: list[dict[str, Any]]):
        for pool in pools:
            if not isinstance(pool, dict):
                raise ValueError(f'pool must be an instance of dict, got {type(pool)} instead')
            token0 = Token(**pool['base_token'])
            token1 = Token(**pool['quote_token'])
            av_quote_asset = ['WETH', 'USDC', 'DAI', 'USDT', 'WMATIC', 'USDC.E', 'WBTC']
            if token1.symbol in av_quote_asset:
                self.add_pair(token0, token1)
            else:
                if token0.symbol in av_quote_asset:
                    self.add_pair(token1, token0)


    def build_and_send_tx(self, function: ContractFunction, tx_params, private_key):
        """
        Build and send transaction
        @param function: ContractFunction to make a transaction
        @param tx_params: a dictionary which usually contains
        {"chainId": chain_id,
         "from": your_address, "gas": gas, "nonce": transaction count,
         'maxFeePerGas': Maximum amount the user is willing to pay,
         'maxPriorityFeePerGas': Miner Tip as it is paid directly to block producers
        @param private_key: your private key
        @return: transaction hash
        @raise: AttributeError if provided function is not a ContractFunction type
                ValueError if provided tx_params doesn't contain a "gas"
        """
        if not isinstance(function, ContractFunction):
            raise AttributeError("Function must be a ContractFunction type!")
        if "gas" not in tx_params:
            raise ValueError("Gas must pe provided in tx_params")
        transaction = function.build_transaction(tx_params)
        signed_tx = self.web3_client.eth.account.sign_transaction(
            transaction, private_key=private_key
        )
        tx_hash = self.web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3_client.to_hex(tx_hash)

    def get_router_approval(self, token: Token, amount, tx_params, private_key):
        """
        Get approve for a router contract
        @param token: Token obj that you want to be approved
        @param amount: float amount you want to approve
        @param tx_params:
        @param private_key:
        @param tx_params: a dictionary which usually contains
        {"chainId": chain_id,
         "from": your_address, "gas": gas, "nonce": transaction count,
         'maxFeePerGas': Maximum amount the user is willing to pay,
         'maxPriorityFeePerGas': Miner Tip as it is paid directly to block producers
        @param private_key: your private key
        @return: transaction hash
        """
        token_contract = get_contract(self.web3_client, "General/ERC20", address=token.address)
        converted_amount = int(amount * 10**token.decimals)
        approve_func = token_contract.functions.approve(self.router.address, converted_amount)
        return self.build_and_send_tx(approve_func, tx_params, private_key)





    @staticmethod
    def _deadline():
        return int(time.time()) + 60
