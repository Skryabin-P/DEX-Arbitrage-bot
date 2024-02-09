import time
from web3 import Web3, AsyncWeb3
import json
from pathlib import Path
from web3.types import ABIFunction
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
    contract_addresses_directory = f'{os.path.dirname(os.path.abspath(__file__))}/' \
                                   f'ABI/{abi_path}/contract_addresses.json'
    with open(contract_addresses_directory, 'r') as file:
        contract_addresses = json.load(file)
        if contract_name not in contract_addresses.keys():
            raise ValueError(f"{contract_name} not found in {contract_addresses_directory}\n"
                             f"Try to add manually or provide a contract address")
        net = net.upper()
        if net not in contract_addresses[contract_name].keys():
            raise ValueError(f"Network `{net}` not added yet for a contract {contract_name}\n"
                             f"Try to add manually to {contract_addresses_directory}"
                             f"\nor provide a contract address")

        subnet = subnet.upper()
        if subnet not in contract_addresses[contract_name][net].keys():
            raise ValueError(f"Subnet `{subnet}` not added yet for `{net}` network for a contract {contract_name}\n"
                             f"Try to add manually to {contract_addresses_directory}"
                             f"\nor provide a contract address")

        address = contract_addresses[contract_name][net][subnet]
    return address


def get_contract(w3: Web3 | AsyncWeb3, abi_name: str,
                 net: str = None, subnet: str = None,  address=None):
    if address is None:
        address = get_contract_address(abi_name, net, subnet)
    if not w3.is_address(address):
        raise ValueError(f"contract address must be hexadecimal and starts with 0x,"
                         f"\ngot `{address}` instead")
    address = w3.to_checksum_address(address)
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

    load_dotenv()
    INFURA_MAINNET = os.environ['INFURA_MAINNET']
    client = UniswapV2("Ethereum", "MAINNET", web3_provider=INFURA_MAINNET)
    usdc = get_contract(client.web3_client, 'General/multicall', "Ethereum", "Mainnet")
    print(usdc.functions.decimals().call())

