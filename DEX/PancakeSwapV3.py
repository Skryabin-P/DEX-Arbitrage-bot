from DEX.SushiSwapV3 import SushiSwapV3


class PancakeSwapV3(SushiSwapV3):
    quoter_ver = "v2"
    multicall_abi = "General/multicall"
    abi_folder = "PancakeSwapV3"
    router_abi = 'SushiSwapV3/SwapRouter'


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from utils import get_function_abi
    import time

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
