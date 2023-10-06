from web3 import Web3


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

