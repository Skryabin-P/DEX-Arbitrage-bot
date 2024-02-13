from web3._utils.abi import get_abi_output_types
from DEX.BaseExchange import BaseExchange
from DEX.BaseToken import BaseToken
from DEX.utils import get_function_abi
from numbers import Real


class UniswapV2(BaseExchange):
    router_abi = 'UniswapV2/Router02'
    factory_abi = 'UniswapV2/Factory'

    def __init__(self, network, subnet, web3_provider=None, pairs=None):
        super().__init__(network, subnet, web3_provider, pairs)
        self._router_output_types = None

    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.router.functions.WETH().call()
        return self._weth_addr

    def _encode_sell_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: Real = 1):
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
        route = [base_asset.address, quote_asset.address, ]
        return self.router.encodeABI(fn_name='getAmountsIn',
                                     args=(converted_amount, route))

    def _encode_buy_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: Real = 1):
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

    def encode_buy_order(self, base_asset: BaseToken, quote_asset: BaseToken,
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
        @return: data for calling multical contract,
        for getting quotes from router02 contract via multicall,
        contains list of tuples (calling_address, encoded data )
        """
        # amount means amount of coins
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

    def decode_multicall_router(self, multicall_raw_data):
        # decode multicall output data and put price data to a quotes dictionary
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
        # Calls multicall and put prices to price_book property
        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, self.router_calls).call()
        self.price_book = self.decode_multicall_router(multicall_raw_data)


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    net = "Ethereum"
    subnet = "MAINNET"
    w3_provider = os.environ['INFURA_MAINNET']
    client = UniswapV2(net, subnet, w3_provider)
    client.pair_list = ['WETH-USDC', 'WBTC-Usdc']
    print(client.pair_list)

