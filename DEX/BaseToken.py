class BaseToken:
    """Base for tokens """
    def __init__(self, name, address, symbol, decimals ):
        self.name = name
        self.address = address
        self.symbol = symbol
        self.decimals = decimals