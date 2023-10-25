import time
from web3._utils.abi import get_abi_output_types
from BaseExchange import BaseExchange
from BaseToken import BaseToken
from utils import get_contract
import requests


class UniswapExchange(BaseExchange):
    def __init__(self, network, fee=None):
        super().__init__(network, fee)
        self._weth_addr = None
        self._pair_list = None
        self._quoter = None
        self._multicall = None
        self._quoter_output_types = None

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

    def _aggregate_quoter_calls(self, amount) -> list[tuple]:
        # amount means amount of coins
        _quoter_calls = []
        for tokens in self.pair_list.values():
            base_asset = BaseToken(**tokens['base_asset'])
            quote_asset = BaseToken(**tokens['quote_asset'])
            buy_call = self._encode_buy_price_func(base_asset, quote_asset, amount)
            sell_call = self._encode_sell_price_func(base_asset, quote_asset, amount)
            _quoter_calls.append((self.quoter.address, buy_call))
            _quoter_calls.append((self.quoter.address, sell_call))
        return _quoter_calls

    def update_price_book(self, amount):
        quotes = {}
        print('Update price book')
        t1 = time.perf_counter()
        quoter_calls = self._aggregate_quoter_calls(amount)

        multicall_raw_data = self.multicall.functions.tryAggregate(
            False, quoter_calls).call()
        for i in range(0, len(multicall_raw_data), 2):
            buy_price = self.web3_client.codec.decode(
                self.quoter_output_types, multicall_raw_data[i][1])[0]
            sell_price = self.web3_client.codec.decode(
                self.quoter_output_types, multicall_raw_data[i + 1][1])[0]

            pair = list(self.pair_list.keys())[i // 2]
            quote_asset_decimals = self.pair_list[pair]['quote_asset'].get('decimals')
            quotes[pair] = {'buy_price': buy_price / 10**int(quote_asset_decimals),
                            'sell_price': sell_price / 10**int(quote_asset_decimals)}

        self.price_book = quotes
        t2 = time.perf_counter()
        print(f'It took {t2 - t1}s')

    def _fetch_top_volume_pools(self, pools_number: int):

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
            top_pools = self._fetch_top_volume_pools(100)
            for pool in top_pools['data']['pools']:
                pair_name = f"{pool['token0']['symbol']}-{pool['token1']['symbol']}"
                address0 = self.web3_client.to_checksum_address(pool['token0']['id'])
                address1 = self.web3_client.to_checksum_address(pool['token1']['id'])
                if pair_name not in self._pair_list.keys():
                    token0 = {'name': pool['token0']['name'],
                              'address': address0,
                              'symbol': pool['token0']['symbol'],
                              'decimals': pool['token0']['decimals']}
                    token1 = {'name': pool['token1']['name'],
                              'address': address1,
                              'symbol': pool['token1']['symbol'],
                              'decimals': pool['token1']['decimals']}
                    self._pair_list[pair_name] = {'base_asset': token0, 'quote_asset': token1}
        return self._pair_list


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    from utils import get_function_abi

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
    t1 = time.perf_counter()
    client = UniswapExchange(net, fee=500)

    print(client.pair_list)
    client.update_price_book(1)
    print(client.price_book)
    time.sleep(1)
    client.update_price_book(1)
    print(client.price_book)

    # TODO: Try to use multicall not async , drop async if multicall is better - DONE
    # TODO: Think about gas fee...
    # TODO:

