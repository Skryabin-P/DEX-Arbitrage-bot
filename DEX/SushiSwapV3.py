from DEX.UniswapV3 import UniswapV3
from DEX.Token import Token

class SushiSwapV3(UniswapV3):
    quoter_ver = "v2"
    abi_folder = "SushiSwapV3"
    multicall_abi = "General/multicall"
    router_abi = 'SushiSwapV3/SwapRouter'

    def encode_buy_order(self, base_asset: Token, quote_asset: Token,
                         amount_in, amount_out, address_to, slippage):
        """
        @param base_asset: first token in pair
        @param quote_asset: second token in pair
        @param amount_in: quote asset token amount to buy
        @param amount_out: desired base asset token amount out
        @param address_to: address to account out tokens
        @param slippage: a float from 0 to 1, set the maximum difference
        between expected amount and minimum amount out
        @return: encoded swapExactTokensForTokens function of router contract,
        amount_out_min(with slippage)
        """
        if slippage < 0 or slippage > 1:
            raise ValueError("Slippage must be from 0 to 1")

        amount_in = int(amount_in * 10 ** quote_asset.decimals)
        amount_out = int(amount_out * 10 ** base_asset.decimals)
        amount_out_min = int((1 - slippage) * amount_out)
        router_struct = {
            "tokenIn": quote_asset.address,
            "tokenOut": base_asset.address,
            "fee": self.fee,
            "recipient": address_to,
            "deadline": self._deadline(),
            "amountIn": amount_in,
            "amountOutMinimum": amount_out_min,
            "sqrtPriceLimitX96": 0,
        }
        return self.router.encodeABI(fn_name='exactInputSingle',
                                     args=[router_struct]), amount_out_min / 10 ** base_asset.decimals


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ['INFURA_MAINNET']

    client = SushiSwapV3('Polygon', 'MAINNET', fee=3000,
                         )
    client.pair_list = ['WMATIC-WETH']
    pair = client.pair_list['WMATIC-WETH']
    encoded = client.encode_buy_order(pair['base_asset'], pair['quote_asset'], 0.004496726383193035,
                            11.65
    )
    print(encoded)

