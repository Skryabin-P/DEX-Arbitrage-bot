from DEX.UniswapV3 import UniswapV3
from DEX.BaseToken import BaseToken

class SushiSwapV3(UniswapV3):
    quoter_ver = "v2"
    abi_folder = "SushiSwapV3"
    multicall_abi = "General/multicall"
    router_abi = 'SushiSwapV3/SwapRouter'
    def encode_buy_order(self, base_asset: BaseToken, quote_asset: BaseToken, amount_in, amount_out):
        amount_in = int(amount_in * 10 ** quote_asset.decimals)
        amount_out = int(amount_out * 10 ** base_asset.decimals)
        amount_out_min = int((1 - self.slippage) * amount_out)
        router_struct = {
            "tokenIn": quote_asset.address,
            "tokenOut": base_asset.address,
            "fee": self.fee,
            "recipient": self.arbitrage_contract.address,
            "deadline": self._deadline(),
            "amountIn": amount_in,
            "amountOutMinimum": amount_out_min,
            "sqrtPriceLimitX96": 0,

        }
        return self.router.encodeABI(fn_name='exactInputSingle',
                                     args=[router_struct]), amount_out_min / 10 ** base_asset.decimals

    def encode_sell_order(self, base_asset: BaseToken, quote_asset: BaseToken, amount_in, amount_out):
        amount_out = int(amount_out * 10 ** quote_asset.decimals)
        amount_in = int(amount_in * 10 ** base_asset.decimals)

        amount_in_max = int((1 + self.slippage) * amount_in)
        router_struct = {
            "tokenIn": base_asset.address,
            "tokenOut": quote_asset.address,
            "fee": self.fee,
            "recipient": self.arbitrage_contract.address,
            "deadline": self._deadline(),
            "amountOut": amount_out,
            "amountInMaximum": amount_in_max,
            "sqrtPriceLimitX96": 0,
        }
        return self.router.encodeABI(fn_name='exactOutputSingle',
                                     args=[router_struct]), amount_out / amount_out ** quote_asset.decimals

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from utils import get_function_abi
    import time

    load_dotenv()
    api_key = os.environ['INFURA_API_KEY']

    client = SushiSwapV3('Polygon', 'MAINNET', fee=3000, api_key=api_key, slippage=0.001
                         )
    client.pair_list = ['WMATIC-WETH']
    pair = client.pair_list['WMATIC-WETH']
    encoded = client.encode_buy_order(pair['base_asset'], pair['quote_asset'], 0.004496726383193035,
                            11.65
    )
    print(encoded)

