import web3


class BaseToken:
    """Base for tokens """
    def __init__(self, *args, **kwargs):
        """
        @param args:
        symbol (str): Short name of a token
        address (str): Token address in hexadecimal format
        decimals (int): The number of decimal places used to represent the token's smallest unit
        @param kwargs:
        symbol (str): Short name of a token
        address (str): Token address in hexadecimal format
        decimals (int): The number of decimal places used to represent the token's smallest unit
        """
        if args:
            if len(args) < 3:
                raise AttributeError(f"BaseToken expected at least 3 positional arguments but {len(args)} was given")
            self.symbol = args[0]
            self.address = args[1]
            self.decimals = args[2]
        if kwargs:
            required_kwargs = ('symbol', 'address', 'decimals')
            for arg in required_kwargs:
                if arg not in kwargs.keys():
                    raise AttributeError(f"BaseToken required `{arg}` argument")
            self.symbol = kwargs['symbol']
            self.address = kwargs['address']
            self.decimals = kwargs['decimals']

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

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, symbol):
        if not isinstance(symbol, str):
            raise ValueError('Symbol must be a string!')
        self._symbol = symbol.upper()


if __name__ == "__main__":
    kw = {'symbol': 'tEst', 'decimals': '6', 'address': '0xfaC38532829fDD744373fdcd4708Ab90fA0c4078'}
    token = BaseToken(**kw)
    print(token.symbol)
    print(token.address)
    print(token.decimals)
