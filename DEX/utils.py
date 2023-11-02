import time
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


def get_contract_address(abi_name: str):
    contract_name = Path(abi_name).name
    abi_path = Path(abi_name).parent

    with open(f'{os.path.dirname(os.path.abspath(__file__))}/'
              f'ABI/{abi_path}/contract_addresses.json', 'r') as file:
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
    import os
    from BaseToken import BaseToken
    from UniswapV3 import UniswapV3

    # quotes_input_abi = get_function_abi('Uniswap-v3/Quoter', 'quoteExactInputSingle')
    # print(encode_function_abi(quotes_input_abi))
    load_dotenv()
    INFURA_MAINNET = os.environ['INFURA_MAINNET']
    # INFURA_API_KEY = os.environ['INFURA_API_KEY']
    # w3 = Web3(Web3.HTTPProvider(INFURA_MAINNET))
    # contr = get_contract(w3, abi_name='Uniswap-v3/Quoter')
    # client = UniswapV3(INFURA_MAINNET)
    # print(client.weth_addr)
    # base_asset = BaseToken(name="WETH", address=client.weth_addr, decimals=18)
    # quote_asset = BaseToken(name="USDT", address="0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    #                         decimals=6)
    # a = contr.functions.quoteExactInputSingle(base_asset.address, quote_asset.address, 3000, 1000000000000000, 0).call()
    # print(a)
    w3 = Web3(Web3.HTTPProvider(INFURA_MAINNET))
    usdt_contract = get_contract(w3, abi_name='ERC20/erc20',
                                 address=w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"))
    weth_contract = get_contract(w3, abi_name='ERC20/erc20',
                                 address=w3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"))

    amount_usdt3000 = usdt_contract.functions.balanceOf(
        w3.to_checksum_address("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36")).call() / 10 ** 6
    amount_weth3000 = weth_contract.functions.balanceOf(
        w3.to_checksum_address("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36")).call() / 10 ** 18

    amount_usdt500 = usdt_contract.functions.balanceOf(
        w3.to_checksum_address("0x11b815efb8f581194ae79006d24e0d814b7697f6")).call() / 10 ** 6
    amount_weth500 = weth_contract.functions.balanceOf(
        w3.to_checksum_address("0x11b815efb8f581194ae79006d24e0d814b7697f6")).call() / 10 ** 18

    amount_usdt1000 = usdt_contract.functions.balanceOf(
        w3.to_checksum_address("0x11b815efb8f581194ae79006d24e0d814b7697f6")).call() / 10 ** 6
    amount_weth1000 = weth_contract.functions.balanceOf(
        w3.to_checksum_address("0x11b815efb8f581194ae79006d24e0d814b7697f6")).call() / 10 ** 18

    sum_weth = amount_weth500 + amount_weth3000
    sum_usdt = amount_usdt500 + amount_usdt3000

    print(sum_usdt / sum_weth)
    # print(contr.encodeABI(fn_name='quoteExactInputSingle', args=('0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6','0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',500, 10000,0) ))
# ValueError: Unknown unit.  Must be one of wei/kwei/babbage/femtoether/mwei/lovelace/picoether/gwei/shannon/nanoether/nano/szabo/microether/micro/finney/milliether/milli/ether/kether/grand/mether/gether/tether
