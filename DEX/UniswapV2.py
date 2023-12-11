import time
from web3._utils.abi import get_abi_output_types
from DEX.BaseExchange import BaseExchange
from DEX.BaseToken import BaseToken
from DEX.utils import get_contract, exec_time, get_function_abi
import requests
from numbers import Real


class UniswapV2(BaseExchange):
    router_abi = 'Uniswap-v2/Router02'
    factory_abi = 'Uniswap-v2/Factory'

    def __init__(self, network, subnet, api_key=None, web3_provider=None, slippage=None, num_pairs: int = 10):
        super().__init__(network, subnet, api_key, web3_provider, slippage)
        self.num_pairs = num_pairs
        self._router = None
        self._multicall = None
        self._router_calls = None
        self._router_output_types = None
        self._graph_endpoint = None
        self._web3_provider = None

    @property
    def router(self):
        if self._router is None:
            self._router = get_contract(self.web3_client, abi_name=self.router_abi,
                                        net=self.network, subnet=self.subnet)
        return self._router



    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.router.functions.WETH().call()
        return self._weth_addr

    def _encode_sell_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: Real = 1):
        """
        returns encoded  sell function for pushing to multicall contract
        """
        converted_amount = int(amount * 10 ** quote_asset.decimals)
        route = [base_asset.address, quote_asset.address, ]
        return self.router.encodeABI(fn_name='getAmountsIn',
                                     args=(converted_amount, route))

    def _encode_buy_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: Real = 1):
        """
        returns encoded  buy function for pushing to milticall contract
        """
        converted_amount = int(amount * 10 ** quote_asset.decimals)
        route = [quote_asset.address, base_asset.address]
        # print(self.router.functions.getAmountsIn(converted_amount, route).call()[0] / 10 ** quote_asset.decimals)
        return self.router.encodeABI(fn_name='getAmountsOut',
                                     args=(converted_amount, route))

    def encode_sell_order(self, base_asset: BaseToken, quote_asset: BaseToken, amount_in, amount_out):
        converted_amount_in = int(amount_in * 10 ** base_asset.decimals)
        route = [base_asset.address, quote_asset.address]
        converted_amount_out_min = int(amount_out * 10 ** quote_asset.decimals * (1-self.slippage))

        return self.router.encodeABI(fn_name="swapExactTokensForTokens",
                                     args=(converted_amount_in, converted_amount_out_min,
                                           route, self.arbitrage_contract.address,
                                           self._deadline())), converted_amount_out_min

    def encode_buy_order(self, base_asset: BaseToken, quote_asset: BaseToken, amount_in, amount_out):
        converted_amount_in = int(amount_in * 10 ** quote_asset.decimals)
        route = [quote_asset.address, base_asset.address]
        converted_amount_out_min = int(amount_out * 10 ** base_asset.decimals * (1-self.slippage))

        return self.router.encodeABI(fn_name="swapExactTokensForTokens",
                                     args=(converted_amount_in, converted_amount_out_min,
                                           route, self.arbitrage_contract.address,
                                           self._deadline())), converted_amount_out_min

    @property
    def router_calls(self) -> list[tuple]:
        # amount means amount of coins
        if self._router_calls is None:
            self._router_calls = []
            for tokens in self.pair_list.values():
                base_asset = tokens['base_asset']
                quote_asset = tokens['quote_asset']
                quote_currency_amount = self.quote_asset_prices[quote_asset.symbol]
                buy_call = self._encode_buy_price_func(base_asset, quote_asset, quote_currency_amount)
                sell_call = self._encode_sell_price_func(base_asset, quote_asset, quote_currency_amount)
                self._router_calls.append((self.router.address, buy_call))
                self._router_calls.append((self.router.address, sell_call))
        return self._router_calls

    @property
    def router_output_types(self) -> list[str]:
        """
        I decided to use getAmountsIn for getting types,
        because it has the same types as getAmountsOut

        return: list of string representation of types for decoding
        after multicall
        """
        if self._router_output_types is None:
            abi_function = get_function_abi(abi_name=self.router_abi,
                                            func_name='getAmountsIn')
            self._router_output_types = get_abi_output_types(abi_function)
        return self._router_output_types

    def _fetch_top_volume_pairs(self):
        # deprecated
        query = "{pairs(first: %s, orderBy: reserveUSD  orderDirection: desc)" \
                " {id " \
                "token0 {id name symbol decimals }" \
                "token1 { id name symbol decimals } } }" % self.num_pairs

        response = requests.post(self.graph_endpoint, json={'query': query})
        return response.json()

    def decode_multicall_router(self, multicall_raw_data):
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

        #print(f'Update price book for {self.name}')

        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, self.router_calls).call()

        self.price_book = self.decode_multicall_router(multicall_raw_data)





if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    net = "Ethereum"
    subnet = "MAINNET"
    api_key = os.environ['INFURA_API_KEY']
    client = UniswapV2(net, subnet, api_key, 1000.0)
    client.pair_list = ['WETH-USDC', 'WBTC-Usdc']
    print(client.pair_list)
    client.update_price_book()
    print(client.price_book)


