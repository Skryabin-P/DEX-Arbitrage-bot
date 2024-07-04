import requests
import os
import json
from PoolsParser.utils import get_tokens_batches


class PoolsParser:
    def __init__(self, network: str, exchange: str, pg_number: int = 1) -> None:
        self._url = 'https://api.geckoterminal.com/api/v2'
        self._abs_path = os.path.abspath(os.path.dirname(__file__))
        self.pg_number = pg_number
        self.network = network
        self.exchange = exchange
        self._pools_path = f'{self._abs_path}/pools/{self.network}/{self.exchange}.json'
        self._tokens_path = f'{self._abs_path}/tokens/{self.network}/{self.exchange}.json'
        self.pg_number = pg_number


    def _get(self, endpoint: str, params: dict = None) -> json:
        headers = {'Accept': 'application/json;version=20230302'}
        if params is None:
            response = requests.get(self._url + endpoint, headers=headers)
            response.raise_for_status()
            return response.json()

        response = requests.get(self._url + endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    @property
    def exchange(self):
        return self._exchange_name

    @exchange.setter
    def exchange(self, exchange_name: str):

        if exchange_name not in self.available_exchanges:
            raise ValueError(f'Invalid exchange name: {exchange_name}, '
                             f'available exchanges: {",".join(self.available_exchanges)}')
        self._exchange_name = exchange_name

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, network: str):
        if network not in self.available_networks:
            raise ValueError(f'Invalid network: {network} ',
                             f'available networks: {",".join(self.available_networks)}')
        self._network = network

    @property
    def available_exchanges(self):
        available_exchanges = []
        if not os.path.isdir(f'{self._abs_path}/resources'):
            os.mkdir(f'{self._abs_path}/resources')
        if not os.path.isfile(f'{self._abs_path}/resources/available_exchanges_{self.network}.json'):
            endpoint = f'/networks/{self.network}/dexes'
            data = self._get(endpoint)
            with open(f'{self._abs_path}/resources/available_exchanges_{self.network}.json', 'w') as file:
                json.dump(data, file, indent=4)

        with open(f'{self._abs_path}/resources/available_exchanges_{self.network}.json', 'r') as file:
            exchanges = json.load(file)
        for exchange in exchanges['data']:
            available_exchanges.append(exchange['id'])
        return available_exchanges

    @property
    def available_networks(self) -> list:
        available_networks = []
        if not os.path.isdir(f'{self._abs_path}/resources'):
            os.mkdir(f'{self._abs_path}/resources')
        if not os.path.isfile(f'{self._abs_path}/resources/available_networks.json'):
            endpoint = f'/networks'
            data = self._get(endpoint)
            with open(f'{self._abs_path}/resources/available_networks.json', 'w') as file:
                json.dump(data, file, indent=4)

        with open(f'{self._abs_path}/resources/available_networks.json', 'r') as file:
            networks = json.load(file)
        for network in networks['data']:
            available_networks.append(network['id'])
        return available_networks

    def refresh_pools(self) -> json:
        endpoint = f'/networks/{self.network}/dexes/{self.exchange}/pools'
        data = self._get(endpoint, params={'page': self.pg_number})
        raw_pools = data['data']
        if not os.path.isdir(f'{self._abs_path}/pools'):
            os.mkdir(f'{self._abs_path}/pools')
        if not os.path.isdir(f'{self._abs_path}/pools/{self.network}'):
            os.mkdir(f'{self._abs_path}/pools/{self.network}')
        pools = self.prepare_pools_data(raw_pools)
        with open(self._pools_path, 'w') as file:
            json.dump(pools, file, indent=4)

        return pools

    @property
    def pools(self) -> dict:
        if not os.path.isfile(self._pools_path):
            return self.refresh_pools()
        with open(self._pools_path, mode='r') as file:
            pools = json.load(file)
            return pools

    @property
    def tokens(self):
        if not os.path.isfile(self._tokens_path):
            all_tokens = []
            for pool in self.pools.items():
                all_tokens.append(pool[1]['base_token'])
                all_tokens.append(pool[1]['quote_token'])
            batches = get_tokens_batches(all_tokens)
            return self.refresh_tokens(batches)
        with open(self._tokens_path, mode='r') as file:
            tokens = json.load(file)
            return tokens

    @staticmethod
    def prepare_pools_data(raw_pools: list[dict]) -> dict:
        pools = {}
        for pool in raw_pools:
            pools[pool['attributes']['name']] = {
                'pool_address': pool['attributes']['address'],
                'base_token': pool['relationships']['base_token']['data']['id'].split('_')[-1],
                'quote_token': pool['relationships']['quote_token']['data']['id'].split('_')[-1],
            }
        return pools

    def refresh_tokens(self, batches: list):
        endpoint = f'/networks/{self.network}/tokens/multi/'
        raw_tokens = []
        tokens = {}
        for batch in batches:
            raw_tokens_batch = self._get(endpoint + '%2C'.join(batch))['data']
            raw_tokens.extend(raw_tokens_batch)
        for token in raw_tokens:
            tokens[token['attributes']['address']] = {
                'symbol': token['attributes']['symbol'],
                'address': token['attributes']['address'],
                'decimals': token['attributes']['decimals'],
            }

        if not os.path.isdir(f'{self._abs_path}/tokens'):
            os.mkdir(f'{self._abs_path}/tokens')
        if not os.path.isdir(f'{self._abs_path}/tokens/{self.network}'):
            os.mkdir(f'{self._abs_path}/tokens/{self.network}')

        with open(self._tokens_path, 'w') as file:
            json.dump(tokens, file, indent=4)
        return tokens

    @property
    def commission_map(self):
        return {
            '0.01%': 100,
            '0.05%': 500,
            '0.3%': 3000,
            '1%': 10000
        }

    @property
    def top_pools(self):
        top_pools = {100: [], 500: [], 3000: [], 10000: []}
        for pool in self.pools.items():
            if len(pool[0].split()) > 3:
                commission = self.commission_map[pool[0].split()[3]]
            else:
                commission = 3000
            base_token = self.tokens.get(pool[1]['base_token'], None)
            quote_token = self.tokens.get(pool[1]['quote_token'], None)
            if base_token and quote_token:
                temp_pool = {
                    'pool_address': pool[1]['pool_address'],
                    'base_token': base_token,
                    'quote_token': quote_token,
                    'commission': commission
                }
                top_pools[commission].append(temp_pool)

        return top_pools



if __name__ == '__main__':
    uniswap_v3_parser = PoolsParser(exchange='uniswap_v3', network='eth')

    top = uniswap_v3_parser.top_pools

    for t in top:
        print(t)
