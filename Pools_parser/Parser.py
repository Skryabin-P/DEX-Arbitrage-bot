import requests
import os
import json


class Parser:
    def __init__(self, network: str, exchange_name: str, ) -> None:
        self.network = network
        self.exchange_name = exchange_name
        self._url = 'https://api.geckoterminal.com/api/v2'
        self._pools_path = f'pools/{self.network}/{self.exchange_name}.json'

    @property
    def exchange_name(self):
        return self._exchange_name

    @exchange_name.setter
    def exchange_name(self, exchange_name: str):

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
        if not os.path.isdir('resources'):
            os.mkdir('resources')
        if not os.path.isfile(f'resources/available_exchanges_{self.network}.json'):
            endpoint = f'networks/{self.network}/dexes'
            url = f'{self._url}/{endpoint}'
            headers = {'Accept': 'application/json;version=20230302'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            with open(f'resources/available_exchanges_{self.network}.json', 'w') as file:
                json.dump(response.json(), file, indent=4)

        with open(f'resources/available_exchanges_{self.network}.json', 'r') as file:
            exchanges = json.load(file)
        for exchange in exchanges['data']:
            available_exchanges.append(exchange['id'])
        return available_exchanges

    @property
    def available_networks(self) -> list:
        available_networks = []
        if not os.path.isdir('resources'):
            os.mkdir('resources')
        if not os.path.isfile(f'resources/available_networks.json'):
            endpoint = 'networks'
            url = f'{self._url}/{endpoint}'
            headers = {'Accept': 'application/json;version=20230302'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            with open(f'resources/available_networks.json', 'w') as file:
                json.dump(response.json(), file, indent=4)

        with open(f'resources/available_networks.json', 'r') as file:
            networks = json.load(file)
        for network in networks['data']:
            available_networks.append(network['id'])
        return available_networks

    def refresh_pools(self, page_numbers: int) -> json:
        endpoint = f'/networks/{self.network}/dexes/{self.exchange_name}/pools'
        headers = {'Accept': 'application/json;version=20230302'}
        url = f'{self._url}/{endpoint}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        raw_pools = response.json()['data']
        if not os.path.isdir(f'pools'):
            os.mkdir(f'pools')
        if not os.path.isdir(f'pools/{self.network}'):
            os.mkdir(f'pools/{self.network}')
        pools = self.prepare_pools_data(raw_pools)
        with open(f'pools/{self.network}/{self.exchange_name}.json', 'w') as file:
            json.dump(pools, file, indent=4)

        return pools

    @property
    def pools(self):
        if not os.path.isfile(self._pools_path):
            return self.refresh_pools(page_numbers=1)
        with open(self._pools_path, mode='r') as file:
            pools = json.load(file)
            return pools

    @staticmethod
    def prepare_pools_data(raw_pools: list[dict]) -> dict:
        pools = {}
        for pool in raw_pools:
            pools[pool['attributes']['name']] = {
                'pool_address': pool['attributes']['address'],
                'base_token': pool['relationships']['base_token']['data']['id'].split('_')[1],
                'quote_token': pool['relationships']['quote_token']['data']['id'].split('_')[1],
            }
        return pools


if __name__ == '__main__':
    uniswap_v3_parser = Parser(exchange_name='uniswap_v3', network='eth')
    print(uniswap_v3_parser.pools)
