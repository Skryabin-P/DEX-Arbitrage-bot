import time

import web3
from web3 import Web3, AsyncWeb3
import json
from pathlib import Path
from web3.types import ABIFunction, Address
from eth_utils import encode_hex, function_abi_to_4byte_selector
from functools import wraps
import os

def _get_abi(abi_name: str):
    abi_path = f'{os.path.dirname(os.path.abspath(__file__))}' \
               f'/ABI/{abi_name}.json'

    with open(abi_path, 'r') as file:
        abi = json.load(file)
    return abi


def get_contract_address(abi_name: str,
                         net: str, subnet: str):
    contract_name = Path(abi_name).name
    abi_path = Path(abi_name).parent

    with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
              f'ABI/{abi_path}/contract_addresses.json', 'r') as file:
        address = json.load(file)[contract_name][net][subnet]
    return address


def get_contract(w3: Web3 | AsyncWeb3, abi_name: str,
                 net: str, subnet: str,  address=None):
    if address is None:
        address = get_contract_address(abi_name, net, subnet)
    abi = _get_abi(abi_name)
    return w3.eth.contract(address, abi=abi)


def get_function_abi(abi_name, func_name: str) -> ABIFunction:
    abi = _get_abi(abi_name)
    for function in abi:
        if function['type'] == 'function':
            if function['name'].lower() == func_name.lower():
                return function


def encode_function_abi(abi_function: ABIFunction):
    return encode_hex(function_abi_to_4byte_selector(abi_function))


def exec_time(func):
    @wraps(func)
    def exec_time_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f'{func.__name__} took {execution_time}s')
        return result

    return exec_time_wrapper


if __name__ == '__main__':
    from dotenv import load_dotenv

    from DEX.UniswapV2 import UniswapV2

    # quotes_input_abi = get_function_abi('Uniswap-v3/Quoter', 'quoteExactInputSingle')
    # print(encode_function_abi(quotes_input_abi))
    load_dotenv()
    INFURA_MAINNET = os.environ['INFURA_API_KEY']
    client = UniswapV2("Etherium", "MAINNET", INFURA_MAINNET)
    print(client.factory.functions.allPairsLength().call())
    # pair_created_event_signature = client.web3_client.keccak(
    #     text="PairCreated (index_topic_1 address token0, index_topic_2 address token1, address pair, uint256 noname)").hex()
    # filter_params = {
    #     'fromBlock': 12000835,
    #     'toBlock': 'latest',
    #
    # }
    # logs = client.factory.events.PairCreated().get_logs(fromBlock=0xE4E57A, toBlock=0xE9B24F)
    #
    # for log in logs:
    #     print(log)
