from web3._utils.abi import get_abi_output_types
from .BaseExchange import BaseExchange
from .Token import Token
from .utils import get_contract, get_function_abi
from numbers import Real


class UniswapV3(BaseExchange):
    """
    Child class of a BaseExchange
    Contains methods for interaction with Uniswap V3 exchange
    """

    def __init__(self, network, subnet, web3_provider=None, fee=None, pairs=None):
        """
        @param network: network name like Ethereum, Arbitrum, etc.
        @param subnet: MAINNET or TESTNET
        @param web3_provider: http/https url for connecting to rpc blockchain node
        @param fee: commission of a pool, one of [100,500,3000,10000]
        @param pairs: List of trading pairs in format "token0_name-token1_name"
        """
        super().__init__(network, subnet, web3_provider, pairs)
        self._quoter = None
        self._quoter_abi_suffix = None
        self._quoter_abi = None
        self._quoter_output_types = None
        self.quoter_ver = "v2"  # quoter_ ver - version of Quoter contract. Only "v1" or "v2" can be set
        self.abi_folder = "UniswapV3"
        self.factory_abi = "UniswapV3/Factory"
        self.multicall_abi = "General/multicall"
        self.router_abi = 'UniswapV3/SwapRouter02'

        self.fee = fee
        self.name = self.__class__.__name__ + '/' + str(self.fee)

    @property
    def fee(self):
        """
        pool fee, may be one of from [100, 500, 3000, 10000] -> [0.01%, 0.05%, 0.3%, 1%]
        @return: pool fee
        """
        return self._fee

    @fee.setter
    def fee(self, fee: int):
        """
        Set fee of the pools
        @param fee: one of [100, 500, 3000, 10000]
        @raise ValueError:
            1. Not an integer
            2. Less than 0
            3. Not one of [100, 500, 3000, 10000]
        """
        if fee is None:
            self._fee = 3000
        else:
            if not isinstance(fee, int):
                raise ValueError('Fee must be an integer')
            if fee < 0:
                raise ValueError('Fee can not be negative')
            possible_fees = [100, 500, 3000, 10000]
            if fee not in possible_fees:
                raise ValueError(f"Fee must be on of {','.join(map(str, possible_fees))}")
            self._fee = fee

    @property
    def quoter_abi_suffix(self):
        """
        Get abi_name suffix for Quoter contract
        Only "v1" or "v2" are possible
        @return: quoter_abi_suffix
        @raise: ValueError: if self.quoter_ver is not "v1" or "v2"
        """
        if self._quoter_abi_suffix is None:
            if self.quoter_ver == "v1":
                self._quoter_abi_suffix = ""
            elif self.quoter_ver == "v2":
                self._quoter_abi_suffix = "V2"
            else:
                raise ValueError(f'quoter_ver might be Only "v1"'
                                 f' or "v2", got {self.quoter_ver} instead')
        return self._quoter_abi_suffix

    @property
    def quoter(self):
        """
        @return: Quoter contract instance
        """
        if self._quoter is None:
            self._quoter = get_contract(self.web3_client,
                                        abi_name=f'{self.abi_folder}/Quoter{self.quoter_abi_suffix}',
                                        net=self.network, subnet=self.subnet)
        return self._quoter

    @property
    def weth_addr(self):
        """
        @return: Wrapped Eth address in Ethereum Network
        or Wrapped Matic address in Polygon Network, etc
        """
        if self._weth_addr is None:
            self._weth_addr = self.quoter.functions.WETH9().call()
        return self._weth_addr

    @property
    def quoter_output_types(self) -> list[str]:
        """
        I decided to use quoteExactInputSingle for getting types,
        because it has the same types as quoteExactOutputSingle

        return: list of string representation of types for decoding
        after multicall
        """
        if self._quoter_output_types is None:
            abi_function = get_function_abi(abi_name=f'{self.abi_folder}/Quoter{self.quoter_abi_suffix}',
                                            func_name='quoteExactInputSingle')
            self._quoter_output_types = get_abi_output_types(abi_function)
        return self._quoter_output_types

    def _encode_sell_price_func(self, base_asset: Token, quote_asset: Token, amount: Real = 1):
        """
        How much base asset tokens we must pass in
        to get exact amount of quote asset tokens

        ver - version of Quoter contract. Only "v1" or "v2" can be set
        @param base_asset: first asset in the pair
        @param quote_asset: second asset in the pair
        @param amount: quote asset token amount
        @return: encoded quoteExactOutputSingle function of a Quoter contract
        to push it in a multicall contract
        """
        converted_amount = int(amount * 10 ** quote_asset.decimals)
        if self.quoter_ver == "v1":
            return self.quoter.encodeABI(fn_name='quoteExactOutputSingle',
                                         args=(base_asset.address,
                                               quote_asset.address,
                                               self.fee, converted_amount, 0))
        elif self.quoter_ver == "v2":
            struct_params = {
                "tokenIn": base_asset.address,
                "tokenOut": quote_asset.address,
                "amount": converted_amount,
                "fee": self.fee,
                "sqrtPriceLimitX96": 0
            }
            return self.quoter.encodeABI(fn_name='quoteExactOutputSingle',
                                         args=[struct_params])
        else:
            raise ValueError(f'quoter_ver might be Only "v1" or "v2", got {self.quoter_ver} instead')

    def _encode_buy_price_func(self, base_asset: Token, quote_asset: Token, amount: Real = 1):
        """
        How much base asset tokens we could get if we pass in
        exact amount of quote asset tokens

        @param base_asset: first asset in the pair
        @param quote_asset: second asset in the pair
        @param amount: quote asset token amount
        @return: encoded quoteExactInputSingle function of a Quoter contract
        to push it in a multicall contract
        """
        converted_amount = int(amount * 10 ** quote_asset.decimals)
        if self.quoter_ver == "v1":
            return self.quoter.encodeABI(fn_name='quoteExactInputSingle',
                                         args=(quote_asset.address,
                                               base_asset.address,
                                               self.fee, converted_amount, 0))

        elif self.quoter_ver == "v2":
            struct_params = {
                "tokenIn": quote_asset.address,
                "tokenOut": base_asset.address,
                "amountIn": converted_amount,
                "fee": self.fee,
                "sqrtPriceLimitX96": 0
            }
            return self.quoter.encodeABI(fn_name='quoteExactInputSingle',
                                         args=[struct_params])
        else:
            raise ValueError(f'quoter_ver might be Only "v1" or "v2", got {self.quoter_ver} instead')

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
        struct = (quote_asset.address, base_asset.address, self.fee,
                  address_to, amount_in, amount_out_min, 0)

        return self.router.encodeABI(fn_name='exactInputSingle',
                                     args=[struct]), amount_out_min / 10 ** base_asset.decimals

    @property
    def quoter_calls(self) -> list[tuple]:
        """
        For every pair in pair_list property we encode functions
        for getting buy and sell prices and put it a list
        @return: data for calling multical contract,
        for getting quotes from Quoter v1 or v2 contract via multicall,
        contains list of tuples (calling_address, encoded data )
        """
        quoter_calls = []
        for tokens in self.pair_list.values():
            base_asset = tokens['base_asset']
            quote_asset = tokens['quote_asset']
            quote_currency_amount = self.quote_asset_prices[quote_asset.symbol]
            buy_call = self._encode_buy_price_func(base_asset, quote_asset, quote_currency_amount)
            sell_call = self._encode_sell_price_func(base_asset, quote_asset, quote_currency_amount)
            quoter_calls.append((self.quoter.address, buy_call))
            quoter_calls.append((self.quoter.address, sell_call))
        return quoter_calls

    def decode_multicall_quoter(self, multicall_raw_data):
        """
        decode multicall output data and put price data to a quotes dictionary
        @param multicall_raw_data: tha data that returns after calling multicall
        @return: quotes dictionary
        """
        quotes = {}
        for i in range(0, len(multicall_raw_data), 2):

            buy_call_success = multicall_raw_data[i][0]
            sell_call_success = multicall_raw_data[i + 1][0]
            pair = list(self.pair_list.keys())[i // 2]  # just pair name
            base_asset_decimals = self.pair_list[pair]['base_asset'].decimals
            quote_asset_symbol = self.pair_list[pair]['quote_asset'].symbol
            if buy_call_success and sell_call_success:
                buy_amount = self.web3_client.codec.decode(
                    self.quoter_output_types,
                    multicall_raw_data[i][1])[0] / 10 ** base_asset_decimals
                sell_amount = self.web3_client.codec.decode(
                    self.quoter_output_types,
                    multicall_raw_data[i + 1][1])[0] / 10 ** base_asset_decimals
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
            False, self.quoter_calls).call()
        self.price_book = self.decode_multicall_quoter(multicall_raw_data)
