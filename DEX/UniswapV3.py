import time
from web3._utils.abi import get_abi_output_types
from BaseExchange import BaseExchange
from BaseToken import BaseToken
from utils import get_contract, exec_time
import requests


class UniswapV3(BaseExchange):
    def __init__(self, network, fee=None):
        super().__init__(network, fee)
        self._quoter = None
        self._multicall = None
        self._quoter_output_types = None
        self._quoter_calls = None

    @property
    def quoter(self):
        # Quoter contract on Uniswap
        if self._quoter is None:
            self._quoter = get_contract(self.web3_client, abi_name='Uniswap-v3/Quoter')
        return self._quoter

    @property
    def multicall(self):
        # Multicall2 contract on Uniswap
        if self._multicall is None:
            self._multicall = get_contract(self.web3_client, abi_name='Uniswap-v3/Multicall2')
        return self._multicall

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
            abi_function = get_function_abi(abi_name='Uniswap-v3/Quoter',
                                            func_name='quoteExactInputSingle')
            self._quoter_output_types = get_abi_output_types(abi_function)
        return self._quoter_output_types

    def _encode_sell_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: float = 1):
        """
        returns encoded  sell function for pushing to milticall contract
        """
        converted_amount = amount * 10 ** base_asset.decimals

        return self.quoter.encodeABI(fn_name='quoteExactInputSingle',
                                     args=(base_asset.address,
                                           quote_asset.address,
                                           self.fee, converted_amount, 0))

    def _encode_buy_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: float = 1):
        """
        returns encoded  buy function for pushing to milticall contract
        """
        converted_amount = amount * 10 ** base_asset.decimals
        return self.quoter.encodeABI(fn_name='quoteExactOutputSingle',
                                     args=(quote_asset.address,
                                           base_asset.address,
                                           self.fee, converted_amount, 0))

    @property
    def quoter_calls(self) -> list[tuple]:
        # amount means amount of coins
        if self._quoter_calls is None:
            self._quoter_calls = []
            for tokens in self.pair_list.values():
                base_asset = tokens['base_asset']
                quote_asset = tokens['quote_asset']
                buy_call = self._encode_buy_price_func(base_asset, quote_asset, 1)
                sell_call = self._encode_sell_price_func(base_asset, quote_asset, 1)
                self._quoter_calls.append((self.quoter.address, buy_call))
                self._quoter_calls.append((self.quoter.address, sell_call))
        return self._quoter_calls

    @exec_time
    def decode_multicall_quoter(self, multicall_raw_data):
        quotes = {}
        for i in range(0, len(multicall_raw_data), 2):
            buy_price = None
            sell_price = None
            buy_call_success = multicall_raw_data[i][0]
            sell_call_success = multicall_raw_data[i + 1][0]
            pair = list(self.pair_list.keys())[i // 2]  # just pair name
            quote_asset_decimals = self.pair_list[pair]['quote_asset'].decimals
            if buy_call_success:
                buy_price = self.web3_client.codec.decode(
                    self.quoter_output_types,
                    multicall_raw_data[i][1])[0] / 10 ** quote_asset_decimals
            if sell_call_success:
                sell_price = self.web3_client.codec.decode(
                    self.quoter_output_types,
                    multicall_raw_data[i + 1][1])[0] / 10 ** quote_asset_decimals

            quotes[pair] = {'buy_price': buy_price,
                            'sell_price': sell_price / 10 ** quote_asset_decimals}
        return quotes

    def update_price_book(self, amount):

        print('Update price book')

        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, self.quoter_calls).call()

        self.price_book = self.decode_multicall_quoter(multicall_raw_data)

    def _fetch_top_volume_pools(self, pools_number: int, network=None):

        query = "{pools(first: %s, orderBy: volumeUSD, " \
                "orderDirection: desc where: {feeTier:%s})" \
                " {id " \
                "token0 {id name symbol decimals }" \
                "token1 { id name symbol decimals } } }" % (pools_number, self.fee)
        graph_endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
        response = requests.post(graph_endpoint, json={'query': query})
        return response.json()

    @property
    def pair_list(self):
        if self._pair_list is None:
            print('Getting pairlist...')
            self._pair_list = {}
            top_pools = self._fetch_top_volume_pools(3)
            for pool in top_pools['data']['pools']:
                pair_name = f"{pool['token0']['symbol']}-{pool['token1']['symbol']}"
                if pair_name not in self._pair_list.keys():
                    token0 = BaseToken(name=pool['token0']['name'],
                                       address=pool['token0']['id'],
                                       symbol=pool['token0']['symbol'],
                                       decimals=pool['token0']['decimals'])
                    token1 = BaseToken(name=pool['token1']['name'],
                                       address=pool['token1']['id'],
                                       symbol=pool['token1']['symbol'],
                                       decimals=pool['token1']['decimals'])
                    self._pair_list[pair_name] = {'base_asset': token0, 'quote_asset': token1}
        return self._pair_list


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    from utils import get_function_abi

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
    t1 = time.perf_counter()
    client = UniswapV3(net, fee=500)

    print(client.pair_list)
    client.update_price_book(1)
    print(client.price_book)
    time.sleep(1)
    client.update_price_book(1)
    print(client.price_book)
    client.update_price_book(1)
    print(client.price_book)
    # TODO: Try to use multicall not async , drop async if multicall is better - DONE
    # TODO: Think about gas fee... seems it can be calculated before transaction sending. QuoterV2 !!!
    #  it returns estimate gas, sqrtprice after and so on
    # TODO: Think about quoter amount, how to calculate , may be set amount in usdt and then transform to tokens amount
    # TODO: May be get balances in pool and take price for only 5-10% in depth for each pair

    # TODO: !!! GET TOKEN PAIRS FOR EVERY NETWORK SEPARATELY

    # TODO: Try to use Quoter v2
