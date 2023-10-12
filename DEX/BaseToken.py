import web3


class BaseToken:
    """Base for tokens """
    def __init__(self, **kwargs):
        self._decimals = None
        self._address = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def decimals(self):
        return self._decimals

    @decimals.setter
    def decimals(self, value):
        if not isinstance(value, int):
            self._decimals = int(value)
        else:
            self._decimals = value

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = web3.Web3.to_checksum_address(value)