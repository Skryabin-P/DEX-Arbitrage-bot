from .UniswapV3 import UniswapV3


class SushiSwapV3(UniswapV3):
    quoter_ver = "v2"
    abi_folder = "SushiSwap-v3"
    graph_endpoint = "https://api.thegraph.com/subgraphs/name/sushi-v3/v3-ethereum"
    multicall_abi = "ERC20/multicall"

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from utils import get_function_abi
    import time

    load_dotenv()
    net = os.environ['INFURA_MAINNET']

    client = SushiSwapV3(net, fee=3000)
    print(client.pair_list)
    client.update_price_book(1)
    print(client.price_book)
    time.sleep(1)
    client.update_price_book(1)
    print(client.price_book)
    client.update_price_book(1)
    print(client.price_book)
