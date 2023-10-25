from web3 import Web3, AsyncWeb3
import json
from pathlib import Path
from web3.types import ABIFunction, Address
from eth_utils import encode_hex, function_abi_to_4byte_selector


def _get_abi(abi_name: str):
    abi_path = f'ABI/{abi_name}.json'

    with open(abi_path, 'r') as file:
        abi = json.load(file)
    return abi

def get_contract_address(abi_name: str):
    contract_name = Path(abi_name).name
    abi_path = Path(abi_name).parent
    with open(f'ABI/{abi_path}/contract_addresses.json', 'r') as file:
        address = json.load(file)[contract_name]
    return address

def get_contract(w3: Web3 | AsyncWeb3, abi_name: str, address=None):
    if address is None:
        address = get_contract_address(abi_name)
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


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    quotes_input_abi = get_function_abi('Uniswap-v3/Quoter', 'quoteExactInputSingle')
    print(encode_function_abi(quotes_input_abi))
    load_dotenv()
    INFURA_MAINNET = os.environ['INFURA_MAINNET']
    INFURA_API_KEY = os.environ['INFURA_API_KEY']
    w3 = Web3(Web3.HTTPProvider(INFURA_MAINNET))
    contr = get_contract(w3, abi_name='Uniswap-v3/Quoter')
    print(contr.encodeABI(fn_name='quoteExactInputSingle', args=('0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6','0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',500, 10000,0) ))
# ValueError: Unknown unit.  Must be one of wei/kwei/babbage/femtoether/mwei/lovelace/picoether/gwei/shannon/nanoether/nano/szabo/microether/micro/finney/milliether/milli/ether/kether/grand/mether/gether/tether
