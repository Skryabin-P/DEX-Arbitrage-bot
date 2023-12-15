import time
from web3._utils.abi import get_abi_output_types
from .BaseExchange import BaseExchange
from .BaseToken import BaseToken
from .utils import get_contract, exec_time, get_function_abi
import requests
from numbers import Real
from eth_utils import to_bytes


class UniswapV3(BaseExchange):
    quoter_ver = "v2"  # quoter_ ver - version of Quoter contract. Only "v1" or "v2" can be set
    abi_folder = "Uniswap-v3"
    factory_abi = "Uniswap-v3/Factory"
    multicall_abi = "ERC20/multicall"
    router_abi = 'Uniswap-v3/SwapRouter02'

    def __init__(self, network, subnet, api_key=None, fee=None, web3_provider=None, slippage=None, num_pairs: int = 10):
        super().__init__(network, subnet, api_key, web3_provider, slippage)
        self.num_pairs = num_pairs
        self._quoter = None
        self._quoter_abi_suffix = None
        self._quoter_abi = None
        self._multicall = None
        self._quoter_output_types = None
        self._quoter_calls = None
        self.fee = fee

    @property
    def fee(self):
        return self._fee

    @fee.setter
    def fee(self, fee: int):
        if fee is None:
            self._fee = 3000
        else:
            if not isinstance(fee, int):
                raise ValueError('Fee must be an integer')
            if fee < 0:
                raise ValueError('Fee can not be negative')
            self._fee = fee

    @property
    def quoter_abi_suffix(self):
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
        # Quoter V1 or V2 contract on Uniswap
        if self._quoter is None:
            self._quoter = get_contract(self.web3_client,
                                        abi_name=f'{self.abi_folder}/Quoter{self.quoter_abi_suffix}',
                                        net=self.network, subnet=self.subnet)
        return self._quoter

    @property
    def weth_addr(self):
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

    def _encode_sell_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: Real = 1):
        """
        ver - version of Quoter contract. Only "v1" or "v2" can be set
        returns encoded  sell function for pushing to multicall contract
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

    def _encode_buy_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: Real = 1):
        """
        returns encoded  buy function for pushing to milticall contract
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

    def encode_sell_order(self, base_asset: BaseToken, quote_asset: BaseToken, amount_in: Real, amount_out):

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

        struct = (base_asset.address, quote_asset.address, self.fee,
                  self.arbitrage_contract.address, amount_out, amount_in_max, 0)

        return self.router.encodeABI(fn_name='exactOutputSingle',
                                     args=[struct]), amount_out / amount_out ** quote_asset.decimals

    def encode_buy_order(self, base_asset: BaseToken, quote_asset: BaseToken, amount_in: Real, amount_out):
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
            "sqrtPriceLimitX96": 0
        }
        struct = (quote_asset.address, base_asset.address, self.fee,
                  self.arbitrage_contract.address, amount_in, amount_out_min, 0)

        return self.router.encodeABI(fn_name='exactInputSingle',
                                     args=[struct]), amount_out_min / 10**base_asset.decimals

    @property
    def quoter_calls(self) -> list[tuple]:
        # amount means amount of coins
        if self._quoter_calls is None:
            self._quoter_calls = []
            for tokens in self.pair_list.values():
                base_asset = tokens['base_asset']
                quote_asset = tokens['quote_asset']
                # if quote_asset.symbol == 'WETH':
                #     print(1)
                quote_currency_amount = self.quote_asset_prices[quote_asset.symbol]
                buy_call = self._encode_buy_price_func(base_asset, quote_asset, quote_currency_amount)
                sell_call = self._encode_sell_price_func(base_asset, quote_asset, quote_currency_amount)
                self._quoter_calls.append((self.quoter.address, buy_call))
                self._quoter_calls.append((self.quoter.address, sell_call))
        return self._quoter_calls

    def decode_multicall_quoter(self, multicall_raw_data):
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
                print(quote_currency_amount)
                buy_price = quote_currency_amount / buy_amount
                sell_price = quote_currency_amount / sell_amount
                quotes[pair] = {'buy_price': buy_price, 'buy_amount': buy_amount,
                                'sell_price': sell_price, 'sell_amount': sell_amount}

        return quotes

    def update_price_book(self):

        # print(f'Update price book for {self.name}')

        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, self.quoter_calls).call()

        self.price_book = self.decode_multicall_quoter(multicall_raw_data)

    def _fetch_top_volume_pools(self):
        # deprecated
        query = "{pools(first: %s, orderBy: volumeUSD, " \
                "orderDirection: desc where: {feeTier:%s})" \
                " {id " \
                "token0 {id name symbol decimals }" \
                "token1 { id name symbol decimals } } }" % (self.num_pairs, self.fee)
        graph_endpoint = self.graph_endpoint
        response = requests.post(graph_endpoint, json={'query': query})
        return response.json()


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ['INFURA_API_KEY']

    # TODO: Try to use multicall not async , drop async if multicall is better - DONE
    # TODO: Think about gas fee... seems it can be calculated before transaction sending. QuoterV2 !!!
    #  it returns estimate gas, sqrtprice after and so on
    # TODO: Think about quoter amount, how to calculate , may be set amount in usdt and then transform to tokens amount
    # TODO: May be get balances in pool and take price for only 5-10% in depth for each pair

    # TODO: !!! GET TOKEN PAIRS FOR EVERY NETWORK SEPARATELY

    # TODO: Try to use Quoter v2 - done!

    # TODO: Add other networks contracts addresses, sub-graphs and add options for picking them
