import time
from web3 import Web3, AsyncWeb3
import json
from pathlib import Path
from web3.types import ABIFunction
from eth_utils import encode_hex, function_abi_to_4byte_selector
from functools import wraps
import os


def _get_abi(abi_name: str):
    """
    @param abi_name: abi name in DEX/ABI directory,
    consisting of a folder name and a file name without json extension
    @return: abi
    """
    abi_path = f'{os.path.dirname(os.path.abspath(__file__))}' \
               f'/ABI/{abi_name}.json'

    with open(abi_path, 'r') as file:
        abi = json.load(file)
    return abi


def get_contract_address(abi_name: str,
                         net: str, subnet: str):
    """
    Search in DEX/ABI/{abi_path}/contract_addresses.json for a contract address
    where {abi_path} is a Folder name with contracts abi
    @param abi_name: abi name in DEX/ABI directory,
    consisting of a folder name and a file name without json extension
    @param net: The network where contract is deployed, like Ethereum, Arbitrum, etc.
    @param subnet: The subnetwork where contract is deployed - MAINNET or TESTNET
    @return: contract address
    @raise ValueError:
        1. If address is not found
        2. If provided network name is not available
        3. If provided subnetwork is not available
    """
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
    """
    @param w3: Web3 instance from web3.py library
    @param abi_name: abi name in DEX/ABI directory,
    consisting of a folder name and a file name without json extension
    @param net: The network where contract is deployed, like Ethereum, Arbitrum, etc.
    @param subnet: The subnetwork where contract is deployed - MAINNET or TESTNET
    @param address: hexadecimal address string of a contract
    @return:  Web3 contract instance
    @raise ValueError: If was provided not correct contract address
    """
    if address is None:
        address = get_contract_address(abi_name, net, subnet)
    if not w3.is_address(address):
        raise ValueError(f"contract address must be hexadecimal and starts with 0x,"
                         f"\ngot `{address}` instead")
    address = w3.to_checksum_address(address)
    abi = _get_abi(abi_name)
    return w3.eth.contract(address, abi=abi)


def get_function_abi(abi_name, func_name: str) -> ABIFunction:
    """
    @param abi_name: abi name in DEX/ABI directory,
    consisting of a folder name and a file name without json extension
    @param func_name: name of the contract function
    @return: abi for the contract function
    """
    abi = _get_abi(abi_name)
    for function in abi:
        if function['type'] == 'function':
            if function['name'].lower() == func_name.lower():
                return function


def encode_function_abi(abi_function: ABIFunction):
    """
    @param abi_function: string abi of a contract function
    @return: hex 4byte selector
    """
    return encode_hex(function_abi_to_4byte_selector(abi_function))


def exec_time(func):
    """
    Measure the function execution time
    @param func: Function you want to measure
    @return: provided function
    """
    @wraps(func)
    def exec_time_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f'{func.__name__} took {execution_time}s')
        return result

    return exec_time_wrapper
