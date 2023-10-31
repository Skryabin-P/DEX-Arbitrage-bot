from UniswapV3 import UniswapV3


class PancakeSwapV3(UniswapV3):
    quoter_ver = "v2"
    graph_endpoint = "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v3-eth"
    multicall_abi = "ERC20/multicall"
    abi_folder = "PancakeSwap-v3"


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from utils import get_function_abi
    import time

    load_dotenv()
    net = os.environ['INFURA_MAINNET']

    client = PancakeSwapV3(net, fee=500)
    print(client.pair_list)
    client.update_price_book(1)
    print(client.price_book)
    time.sleep(1)
    client.update_price_book(1)
    print(client.price_book)
    client.update_price_book(1)
    print(client.price_book)
