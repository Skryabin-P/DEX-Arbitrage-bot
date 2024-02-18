from DEX.UniswapV3 import UniswapV3
from DEX.Token import Token


class SushiSwapV3(UniswapV3):
    """
    Child class of a UniswapV3
    SushiSwap is a fork of UniswapV3
    """

    def __init__(self, network, subnet, web3_provider=None, fee=None, pairs=None):
        """
        @param network: network name like Ethereum, Arbitrum, etc.
        @param subnet: MAINNET or TESTNET
        @param web3_provider: http/https url for connecting to rpc blockchain node
        @param fee: commission of a pool, one of [100,500,3000,10000]
        @param pairs: List of trading pairs in format "token0_name-token1_name"
        """
        super().__init__(network, subnet, web3_provider, fee, pairs)
        self.quoter_ver = "v2"
        self.multicall_abi = "General/multicall"
        self.abi_folder = "SushiSwapV3"
        self.router_abi = "SushiSwapV3/SwapRouter"
        self.factory_abi = 'SushiSwapV3/Factory'

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
