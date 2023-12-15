from eth_abi import encode
from DEX.utils import get_contract
from DEX.UniswapV3 import UniswapV3
from DEX.UniswapV2 import UniswapV2
from DEX.Converter import Converter
from dotenv import load_dotenv
import os
from eth_utils.abi import function_signature_to_4byte_selector
import codecs

print(function_signature_to_4byte_selector("approve(address,uint256)"))

load_dotenv()

converter = Converter('USDT', 1000)

uniswap_v3 = UniswapV3('Polygon', 'MAINNET', fee=3000, api_key=os.environ['INFURA_API_KEY'], slippage=0.01)

#uniswap_v3 = UniswapV2('Ethereum', 'MAINNET',  web3_provider='http://127.0.0.1:7545', slippage=0.1)
#uniswap_v3 = UniswapV3('Ethereum', 'MAINNET', fee=3000,  web3_provider='http://127.0.0.1:7545', slippage=0.1)
print(uniswap_v3.arbitrage_contract.functions.gas_left().call())

uniswap_v3.pair_list = ['WETH-USDT', 'LINK-WETH', 'LINK-USDT']
uniswap_v3.quote_asset_prices = converter.convert()

uniswap_v3.update_price_book()

price_weth_usdc = uniswap_v3.price_book['WETH-USDT']
price_link_weth = uniswap_v3.price_book['LINK-WETH']

weth_usdc = uniswap_v3.pair_list['WETH-USDT']
usdt_address = uniswap_v3.pair_list['WETH-USDT']['quote_asset'].address
function_signature = 'approve(address,uint256)'
usdt_approve = get_contract(uniswap_v3.web3_client, 'ERC20/erc20', 'Ethereum',
                            'MAINNET', weth_usdc['quote_asset'].address).encodeABI(fn_name='approve',
                                                                                   args=(uniswap_v3.router.address,
                                                                                         1000 * 10**6 * 10))
print(1000 * 10**6)
#0x8b069f2a000000000000000000000000c2132d05d31c914a87c6611c10748aeb04b58e8f000000000000000000000000000000000000000000000000000000003b9aca00
print(uniswap_v3.arbitrage_contract.functions.encodeApproves(usdt_address, 1000*10**6).call())
print(uniswap_v3.web3_client.keccak(text="approve(address,uint256)")[:4])


print(usdt_address)
print(usdt_approve)

buy_weth_encoded, weth_amount = uniswap_v3.encode_buy_order(weth_usdc['base_asset'], weth_usdc['quote_asset'], 1000,
                                                            price_weth_usdc['buy_amount'])

link_weth = uniswap_v3.pair_list['LINK-WETH']

weth_approve = get_contract(uniswap_v3.web3_client, 'ERC20/erc20', 'Ethereum',
                            'MAINNET', link_weth['quote_asset'].address).encodeABI(fn_name='approve',
                                                                                   args=(uniswap_v3.router.address,
                                                                                         int(weth_amount*10**18)))

buy_link_encoded, link_amount = uniswap_v3.encode_buy_order(link_weth['base_asset'], link_weth['quote_asset'],
                                                            weth_amount,
                                                            price_link_weth['buy_amount'] * (1 - uniswap_v3.slippage))

# link_usdt_price = uniswap_v3.price_book['LINK-USDT']

link_approve = get_contract(uniswap_v3.web3_client, 'ERC20/erc20', 'Ethereum',
                            'MAINNET', link_weth['base_asset'].address).encodeABI(fn_name='approve',
                                                                                  args=(uniswap_v3.router.address,
                                                                                        int(link_amount*10**link_weth['base_asset'].decimals)))

# sell_link_encoded, _ = uniswap_v3.encode_sell_order(link_weth['base_asset'], weth_usdt['quote_asset'],
# link_amount, link_usdt_price['sell_price'] * link_amount)


# , str.encode(sell_link_encoded)  link_weth['base_asset'].address  str.encode(link_approve) uniswap_v3.router.address


print(buy_weth_encoded)
routers = [uniswap_v3.router.address, uniswap_v3.router.address, ]
trades = [codecs.decode(buy_weth_encoded[2:], 'hex_codec'), codecs.decode(buy_link_encoded[2:], 'hex_codec')]
tokens = [weth_usdc['quote_asset'].address, link_weth['quote_asset'].address, ]
approves = [codecs.decode(usdt_approve[2:], 'hex_codec'), codecs.decode(weth_approve[2:], 'hex_codec')]
print(approves[0])
print(trades[0])
encoded_data = encode(types=['address[]', 'bytes[]', 'address[]', 'bytes[]'],
                      args=[routers, trades, tokens, approves])


encode_addr = encode(types=['address[]', 'bytes[]'],
                     args=[routers, trades])
# print(encode_addr)
# tokens[0], 1000*10**6,

print(uniswap_v3.arbitrage_contract.functions.viewParams(encoded_data).call())



# my_address = os.environ['adr']
# my_private_key = os.environ['prk']
my_address = os.environ['address']
my_private_key = os.environ['private_key']

nonce = uniswap_v3.web3_client.eth.get_transaction_count(my_address)
print(nonce)
chain_id = uniswap_v3.web3_client.eth.chain_id
gas_price = uniswap_v3.web3_client.eth.gas_price
max_fee = uniswap_v3.web3_client.to_wei(60, 'gwei')
max_fee_gas = uniswap_v3.web3_client.to_wei(40, 'gwei')
print(encoded_data.hex())
call_function = uniswap_v3.arbitrage_contract.functions.requestFlashLoan(
    tokens[0], 1000 * 10 ** 6,
    encoded_data).build_transaction({"chainId": chain_id,
                                     "from": my_address, "gas": 700000, "nonce": nonce, 'maxFeePerGas': int(gas_price*1.05),
                                     'maxPriorityFeePerGas': int(gas_price*1)})

print(call_function)

try:
    signed_tx = uniswap_v3.web3_client.eth.account.sign_transaction(call_function, private_key=my_private_key)

    send_tx = uniswap_v3.web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = uniswap_v3.web3_client.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt)
except ValueError as e:
    from eth_abi import decode
    error = str(e).encode()

    print(error)
    revert_message_bytes = error

    revert_message = uniswap_v3.web3_client.to_hex(revert_message_bytes)  # Convert bytes to hex string
    error_msg = decode(['bytes'],
                             uniswap_v3.web3_client.to_bytes(hexstr=revert_message))  # Decode hex string to actual error message

    print(error_msg)


  # Initialize web3 object with your preferred provider

# Revert message bytes received








