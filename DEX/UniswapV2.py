from web3._utils.abi import get_abi_output_types
from DEX.BaseExchange import BaseExchange
from DEX.Token import Token
from DEX.utils import get_function_abi
from numbers import Real


class UniswapV2(BaseExchange):
    """
    Child class of a BaseExchange
    Contains methods for interaction with Uniswap V2 exchange
    """

    def __init__(self, network, subnet, web3_provider=None, pairs=None):
        """
        @param network: network name like Ethereum, Arbitrum, etc.
        @param subnet: MAINNET or TESTNET
        @param web3_provider: http/https url for connecting to rpc blockchain node
        @param pairs: List of trading pairs in format "token0_name-token1_name"
        """
        super().__init__(network, subnet, web3_provider, pairs)
        self.router_abi = 'UniswapV2/Router02'
        self.factory_abi = 'UniswapV2/Factory'
        self._router_output_types = None

    @property
    def weth_addr(self):
        """
        @return: Wrapped Eth address in Ethereum Network
        or Wrapped Matic address in Polygon Network, etc
        """
        if self._weth_addr is None:
            self._weth_addr = self.router.functions.WETH().call()
        return self._weth_addr

    def _encode_sell_price_func(self, base_asset: Token, quote_asset: Token, amount: Real = 1):
        """
        How much base asset tokens we must pass in
        to get exact amount of quote asset tokens

        @param base_asset: first asset in the pair
        @param quote_asset: second asset in the pair
        @param amount: quote asset token amount
        @return: encoded getAmountsIn router contract function
        for pushing to multicall contract
        """
        converted_amount = int(amount * 10 ** quote_asset.decimals)
        route = [base_asset.address, quote_asset.address]
        return self.router.encodeABI(fn_name='getAmountsIn',
                                     args=(converted_amount, route))

    def _encode_buy_price_func(self, base_asset: Token, quote_asset: Token, amount: Real = 1):
        """
        How much base asset tokens we could get if we pass in
        exact amount of quote asset tokens

        @param base_asset: first asset in the pair
        @param quote_asset: second asset in the pair
        @param amount: quote asset token amount
        @return: encoded getAmountsOut router contract function
        for pushing to multicall contract
        """
        converted_amount = int(amount * 10 ** quote_asset.decimals)
        route = [quote_asset.address, base_asset.address]
        return self.router.encodeABI(fn_name='getAmountsOut',
                                     args=(converted_amount, route))

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
        converted_amount_in = int(amount_in * 10 ** quote_asset.decimals)
        route = [quote_asset.address, base_asset.address]
        converted_amount_out_min = int(amount_out * 10 ** base_asset.decimals * (1-slippage))

        return self.router.encodeABI(fn_name="swapExactTokensForTokens",
                                     args=(converted_amount_in, converted_amount_out_min,
                                           route, address_to,
                                           self._deadline())), converted_amount_out_min / 10**base_asset.decimals

    @property
    def router_calls(self) -> list[tuple]:
        """
        For every pair in pair_list property we encode functions
        for getting buy and sell prices and put it a list
        @return: data for calling multical contract
        to get quotes from router02 contract via multicall,
        contains list of tuples (calling_address, encoded data )
        """
        router_calls = []
        for tokens in self.pair_list.values():
            base_asset = tokens['base_asset']
            quote_asset = tokens['quote_asset']
            quote_currency_amount = self.quote_asset_prices[quote_asset.symbol]
            buy_call = self._encode_buy_price_func(base_asset, quote_asset, quote_currency_amount)
            sell_call = self._encode_sell_price_func(base_asset, quote_asset, quote_currency_amount)
            router_calls.append((self.router.address, buy_call))
            router_calls.append((self.router.address, sell_call))
        return router_calls

    @property
    def router_output_types(self) -> list[str]:
        """
        I decided to use getAmountsIn for getting types,
        because it has the same types as getAmountsOut

        return: list of string representation of function
        output types for decoding after multicall
        """
        if self._router_output_types is None:
            abi_function = get_function_abi(abi_name=self.router_abi,
                                            func_name='getAmountsIn')
            self._router_output_types = get_abi_output_types(abi_function)
        return self._router_output_types

    def decode_multicall_router(self, multicall_raw_data) -> dict:
        """
        decode multicall output data and put price data to a quotes dictionary
        @param multicall_raw_data: tha data that returns after calling multicall
        @return: quotes dictionary
        """
        quotes = {}
        for i in range(0, len(multicall_raw_data), 2):
            pair = list(self.pair_list.keys())[i // 2]  # just pair name
            buy_call_success = multicall_raw_data[i][0]
            sell_call_success = multicall_raw_data[i + 1][0]
            base_asset_decimals = self.pair_list[pair]['base_asset'].decimals
            quote_asset_symbol = self.pair_list[pair]['quote_asset'].symbol
            if buy_call_success and sell_call_success:
                buy_amount = self.web3_client.codec.decode(
                        self.router_output_types,
                        multicall_raw_data[i][1])[0][1] / 10 ** base_asset_decimals
                sell_amount = self.web3_client.codec.decode(
                        self.router_output_types,
                        multicall_raw_data[i + 1][1])[0][0] / 10 ** base_asset_decimals
                quote_currency_amount = self.quote_asset_prices[quote_asset_symbol]
                buy_price = quote_currency_amount / buy_amount
                sell_price = quote_currency_amount / sell_amount
                quotes[pair] = {'buy_price': buy_price, 'buy_amount': buy_amount,
                                'sell_price': sell_price, 'sell_amount': sell_amount}
        return quotes

    def update_price_book(self):
        """
        Calls multicall contract to get quotes
        then decode multicall and put quotes dictionary
        to the price_book property
        """
        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, self.router_calls).call()
        self.price_book = self.decode_multicall_router(multicall_raw_data)

    def make_trade(self, token_in: Token, token_out: Token, recipient, amount_in,
                   amount_out, slippage, tx_params, private_key):
        """
        Create and send trading transaction using swapExactTokensForTokens
        function of a Router02 contract

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
        path = [token_in.address, token_out.address]
        trade_params = [converted_amount_in, converted_amount_out_min,
                        path, recipient, self._deadline()]
        trade_func = self.router.functions.swapExactTokensForTokens(trade_params)

        return self.build_and_send_tx(trade_func, tx_params, private_key)
