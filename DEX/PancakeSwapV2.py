from DEX.UniswapV2 import UniswapV2


class PancakeSwapV2(UniswapV2):
    router_abi = "PancakeSwapV2/Router02"


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import time

    load_dotenv()
    api_key = os.environ['INFURA_API_KEY']
    client = PancakeSwapV2("Polygon", "MAINNET", api_key)
    print(client.pair_list)
    client.update_price_book()
    print(client.price_book)

