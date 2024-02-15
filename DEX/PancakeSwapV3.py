from DEX.SushiSwapV3 import SushiSwapV3


class PancakeSwapV3(SushiSwapV3):
    """
    Child class of a SushiSwap V3
    PancakeSwapV3 is also a fork of UniswapV3
    """

    def __init__(self, network, subnet, web3_provider=None, fee=None, pairs=None):
        """
        @param network: network name like Ethereum, Arbitrum, etc
        @param subnet: MAINNET or TESTNET
        @param web3_provider: http/https url for connecting to rpc blockchain node
        @param fee: commission of a pool, one of [100,500,3000,10000]
        @param pairs: List of trading pairs in format "token0_name-token1_name"
        """
        super().__init__(network, subnet, web3_provider, fee, pairs)
        self.quoter_ver = "v2"
        self.multicall_abi = "General/multicall"
        self.abi_folder = "PancakeSwapV3"
        self.router_abi = "PancakeSwapV3/SwapRouter"
        self.factory_abi = 'PancakeSwapV3/Factory'
