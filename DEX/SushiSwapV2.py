from DEX.UniswapV2 import UniswapV2


class SushiSwapV2(UniswapV2):
    """
    Child class of a UniswapV2
    SushiSwapV2 is also a fork of UniswapV2
    """

    def __init__(self, network, subnet, web3_provider=None, pairs=None):
        """
        @param network: network name like Ethereum, Arbitrum, etc
        @param subnet: MAINNET or TESTNET
        @param web3_provider: http/https url for connecting to rpc blockchain node
        @param pairs: List of trading pairs in format "token0_name-token1_name"
        """
        super().__init__(network, subnet, web3_provider, pairs)
        self.router_abi = "SushiSwapV2/Router02"
        self.factory_abi = 'SushiSwapV2/Factory'
