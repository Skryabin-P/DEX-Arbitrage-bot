from web3 import Web3, AsyncWeb3
from web3.types import HexStr, ABIFunction
from utils import get_contract, get_function_abi, encode_function_abi, get_contract_address
from BaseToken import BaseToken
import asyncio
from web3._utils.contracts import encode_abi
from web3._utils.abi import get_abi_output_types
from dataclasses import dataclass

class BaseExchange:
    def __init__(self, network, fee=None):
        self.network = network
        self.web3_client = Web3(Web3.HTTPProvider(self.network))
        self.web3_client_async = AsyncWeb3(Web3.AsyncHTTPProvider(self.network))
        self.fee = fee
        self._price_book = None
        self._pair_list = None
        self._weth_addr = None
    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, network):
        self._network = network

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

    def get_token(self, address: str, abi_name='erc20'):
        """
        Retrieves info about a ERC20 contract of a given token
        name, symbol, and decimals.
        """
        token_contract = get_contract(self.web3_client, abi_name=abi_name, address=address)
        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
        return BaseToken(name=name, address=address, symbol=symbol, decimals=decimals)

    async def get_token_async(self, address: str, abi_name='erc20'):
        """
        Retrieves info about a ERC20 contract of a given token
        name, symbol, and decimals.
        """
        token_contract = get_contract(self.web3_client_async, abi_name=abi_name, address=address)
        task_name = asyncio.create_task(token_contract.functions.name().call())
        task_symbol = asyncio.create_task(token_contract.functions.symbol().call())
        task_decimals = asyncio.create_task(token_contract.functions.decimals().call())
        name = await task_name
        symbol = await task_symbol
        decimals = await task_decimals
        return BaseToken(name=name, address=address, symbol=symbol, decimals=decimals)

    def get_contract_func(self, abi_name, func_name, contract_address=None):
        abi_function = get_function_abi(f'ABI/{abi_name}', func_name)
        function_output_types = get_abi_output_types(abi_function)
        function_selector = encode_function_abi(abi_function)
        if contract_address is None:
            contract_address = get_contract_address(abi_name)
        contract_address = self.web3_client.to_checksum_address(contract_address)
        return ContractFunction(abi_function, function_output_types,
                                function_selector, contract_address)


@dataclass
class ContractFunction:
    abi_function: ABIFunction
    output_types: list[str]
    selector: HexStr
    address: str


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    import time
    load_dotenv()
    exchange_async = BaseExchange(os.environ['INFURA_MAINNET'])
    t1 = time.perf_counter()

    async def main_async():
        token = await exchange_async.get_token_async('0xdAC17F958D2ee523a2206206994597C13D831ec7')
        print(token.name)
    asyncio.run(main_async())
    t2 = time.perf_counter()
    print(t2-t1)

    t1 = time.perf_counter()
    exchange = BaseExchange(os.environ['INFURA_MAINNET'])
    token = exchange.get_token('0xdAC17F958D2ee523a2206206994597C13D831ec7')
    print(token.name)
    t2 = time.perf_counter()

    print(t2-t1)