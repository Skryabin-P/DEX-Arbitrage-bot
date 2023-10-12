from web3 import Web3, AsyncWeb3
from utils import get_contract
from BaseToken import BaseToken
import asyncio


class BaseExchange:
    def __init__(self, network, fee=None):
        self.network = network
        self.web3_client = Web3(Web3.HTTPProvider(self.network))
        self.web3_client_async = AsyncWeb3(Web3.AsyncHTTPProvider(self.network))
        self.fee = fee

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