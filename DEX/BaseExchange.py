from web3 import Web3
from utils import get_contract
from BaseToken import BaseToken


class BaseExchange:
    def __init__(self, network, fee=None):
        self.network = network
        self.web3_client = Web3(Web3.HTTPProvider(self.network))
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
        return name, symbol, decimals

