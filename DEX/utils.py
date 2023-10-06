from web3 import Web3
import json
from pathlib import Path

def _get_abi(abi_name: str):
    abi_path = f'ABI/{abi_name}.json'

    with open(abi_path,'r') as file:
        abi = json.load(file)
    return abi

def get_contract(w3: Web3, abi_name: str):
    contract_name = Path(abi_name).name
    abi_path = Path(abi_name).parent
    with open(f'ABI/{abi_path}/contract_addresses.json', 'r') as file:
        address = json.load(file)[contract_name]
    abi = _get_abi(abi_name)
    return w3.eth.contract(address, abi=abi)

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os


    load_dotenv()
    INFURA_MAINNET = os.environ['INFURA_MAINNET']
    INFURA_API_KEY = os.environ['INFURA_API_KEY']

    w3 = Web3(Web3.HTTPProvider(INFURA_MAINNET))
    print(f'Connect status: {w3.is_connected()}')
    quoter_contract_address = '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6'
    quoter_contract = get_contract(w3, abi_name='Uniswap-v3/Quoter')
    chainlink_adr = w3.to_checksum_address('0x514910771AF9Ca656af840dff83E8264EcF986CA')
    eth_adr = quoter_contract.functions.WETH9().call()
    usdt_adr = w3.to_checksum_address('0xdAC17F958D2ee523a2206206994597C13D831ec7')
    # print(usdt_adr)
    #print()
    amount = 1 * 10 ** 18
    amount_chainlink = 1 * 10**8
    price_sell = quoter_contract.functions.quoteExactInputSingle(chainlink_adr,usdt_adr, 3000, amount, 0).call()
    price_buy = quoter_contract.functions.quoteExactOutputSingle(usdt_adr, chainlink_adr, 3000, amount, 0).call()
    print(f"Price sell {w3.from_wei(price_sell, 'mwei')}")
    print(f"Price buy {w3.from_wei(price_buy,'mwei')}")
# ValueError: Unknown unit.  Must be one of wei/kwei/babbage/femtoether/mwei/lovelace/picoether/gwei/shannon/nanoether/nano/szabo/microether/micro/finney/milliether/milli/ether/kether/grand/mether/gether/tether