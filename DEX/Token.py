import web3


class Token:
    """
    Class for ERC20 tokens
    Contains properties describing
    base parameters of a ERC20 token
    """
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
            required_kwargs = {'symbol', 'address', 'decimals'}

            if not set(kwargs.keys()).issuperset(required_kwargs):
                raise AttributeError(f"BaseToken required {','.join(required_kwargs)} mandatory keyword arguments,"
                                     f" but {','.join(kwargs.keys())} was given")
            self.symbol = kwargs['symbol']
            self.address = kwargs['address']
            self.decimals = kwargs['decimals']

    @property
    def decimals(self):
        """
        The number of decimals a token has
        @return: decimals
        """
        return self._decimals

    @decimals.setter
    def decimals(self, decimal_num):
        """
        Set the decimals' property
        @param decimal_num: the decimal numbers of a token
        """
        if not isinstance(decimal_num, int):
            self._decimals = int(decimal_num)
        else:
            self._decimals = decimal_num

    @property
    def address(self):
        """
        @return: checksum token address string
        """
        return self._address

    @address.setter
    def address(self, address):
        """
        @param address: hexadecimal token address string
        @raise ValueError: if address is not correct
        """
        if not web3.Web3.is_address(address):
            raise ValueError(f"Address must be must be a hex string starting with 0x")
        self._address = web3.Web3.to_checksum_address(address)

    @property
    def symbol(self):
        """
        @return: symbol name
        """
        return self._symbol

    @symbol.setter
    def symbol(self, symbol):
        """
        @param symbol: name of a symbol, like WETH, USDT, etc.
        @raise ValueError: if provided symbol is not string type
        """
        if not isinstance(symbol, str):
            raise ValueError('Symbol must be a string!')
        self._symbol = symbol.upper()


if __name__ == "__main__":
    kw = {'symbol': 'tEst', 'decimals': '6', 'address': '0xf0245f6251bef9447a08766b9da2b07b28ad80b0'}
    token = Token(**kw)
    print(token.symbol)
    print(token.address)
    print(token.decimals)
