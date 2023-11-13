from DEX.UniswapV2 import UniswapV2


class SushiSwapV2(UniswapV2):
    router_abi = "SushiSwap-v2/Router02"

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import time

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
    client = SushiSwapV2(net)
    print(client.pair_list)
    client.update_price_book(1)
    print(client.price_book)
    time.sleep(1)
    client.update_price_book(1)
    print(client.price_book)
    client.update_price_book(1)
    print(client.price_book)
