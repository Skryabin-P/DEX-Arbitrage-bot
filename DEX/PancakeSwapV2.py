from UniswapV2 import UniswapV2


class PancakeSwapV2(UniswapV2):
    router_abi = "PancakeSwap-v2/Router02"
    graph_endpoint = "https://api.thegraph.com/subgraphs/name/pancakeswap/exhange-eth"


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import time

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
    client = PancakeSwapV2(net)
    print(client.pair_list)
    client.update_price_book(1)
    print(client.price_book)
    time.sleep(1)
    client.update_price_book(1)
    print(client.price_book)
    client.update_price_book(1)
    print(client.price_book)
