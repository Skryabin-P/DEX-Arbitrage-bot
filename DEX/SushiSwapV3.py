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

    def make_trade(self, token_in: Token, token_out: Token, recipient, amount_in,
                   amount_out, slippage, tx_params, private_key):
        """
        Create and send trading transaction using exactInputSingle
        function of a SwapRouter contract

        @param token_in: Token obj that you want to sell
        @param token_out: Token obj that you want to buy
        @param recipient: address which will get tokens after exchange
        @param amount_in: amount of token in
        @param amount_out: desire amount of token out
        @param slippage: from 0 to 1, the difference between the expected price
        of a trade and the price at which the trade is executed
        @param tx_params: a dictionary which usually contains
        {"chainId": chain_id,
         "from": your_address, "gas": gas, "nonce": transaction count,
         'maxFeePerGas': Maximum amount the user is willing to pay,
         'maxPriorityFeePerGas': Miner Tip as it is paid directly to block producers
        @param private_key: private key of your address
        @return: transaction hash
        """
        converted_amount_in = int(amount_in * 10 ** token_in.decimals)
        amount_out_min = (1 - slippage) * amount_out
        converted_amount_out_min = int(amount_out_min * 10 ** token_out.decimals)
        trade_params = [token_in.address, token_out.address, self.fee,
                        recipient, self._deadline(), converted_amount_in, converted_amount_out_min, 0]
        trade_func = self.router.functions.exactInputSingle(trade_params)

        return self.build_and_send_tx(trade_func, tx_params, private_key)