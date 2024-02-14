from DEX.UniswapV2 import UniswapV2


class PancakeSwapV2(UniswapV2):
    """
    Child class of a UniswapV2
    PancakeSwapV2 is a fork of Uniswap V2
    """

    def __init__(self, network, subnet, web3_provider=None, pairs=None):
        super().__init__(network, subnet, web3_provider, pairs)
        self.router_abi = "PancakeSwapV2/Router02"
        self.factory_abi = 'PancakeSwapV2/Factory'
