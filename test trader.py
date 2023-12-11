from eth_abi import encode
from DEX.utils import get_contract
from DEX.UniswapV3 import UniswapV3
from DEX.UniswapV2 import UniswapV2
from DEX.Converter import Converter
from dotenv import load_dotenv
import os

load_dotenv()



converter = Converter('USDT', 1000)

#uniswap_v3 = UniswapV3('Ethereum', 'MAINNET', fee=3000, web3_provider='http://127.0.0.1:7545', slippage=0.1)

uniswap_v3 = UniswapV2('Ethereum', 'MAINNET',  web3_provider='http://127.0.0.1:7545', slippage=0.1)

print(uniswap_v3.arbitrage_contract.functions.gas_left().call())

uniswap_v3.pair_list = ['WETH-USDT', 'LINK-WETH', 'LINK-USDT']
uniswap_v3.quote_asset_prices = converter.convert()

uniswap_v3.update_price_book()


price_weth_usdt = uniswap_v3.price_book['WETH-USDT']
price_link_weth = uniswap_v3.price_book['LINK-WETH']

weth_usdt = uniswap_v3.pair_list['WETH-USDT']

usdt_approve = get_contract(uniswap_v3.web3_client, 'ERC20/erc20', 'Ethereum',
                            'MAINNET', weth_usdt['quote_asset'].address).encodeABI(fn_name='approve',
                                                                                   args=(uniswap_v3.router.address,
                                                                                        1000 * 10 ** 6))

buy_weth_encoded, weth_amount = uniswap_v3.encode_buy_order(weth_usdt['base_asset'], weth_usdt['quote_asset'], 1000,
                                       price_weth_usdt['buy_amount'])


link_weth = uniswap_v3.pair_list['LINK-WETH']

weth_approve = get_contract(uniswap_v3.web3_client, 'ERC20/erc20', 'Ethereum',
                            'MAINNET', link_weth['quote_asset'].address).encodeABI(fn_name='approve',
                                                                                   args=(uniswap_v3.router.address,
                                                                                        weth_amount))




buy_link_encoded, link_amount = uniswap_v3.encode_buy_order(link_weth['base_asset'], link_weth['quote_asset'], weth_amount,
                                       price_link_weth['buy_amount'])

#link_usdt_price = uniswap_v3.price_book['LINK-USDT']

link_approve = get_contract(uniswap_v3.web3_client, 'ERC20/erc20', 'Ethereum',
                            'MAINNET', link_weth['base_asset'].address).encodeABI(fn_name='approve',
                                                                                   args=(uniswap_v3.router.address,
                                                                                        link_amount))

#sell_link_encoded, _ = uniswap_v3.encode_sell_order(link_weth['base_asset'], weth_usdt['quote_asset'],
                                                  # link_amount, link_usdt_price['sell_price'] * link_amount)


# , str.encode(sell_link_encoded)  link_weth['base_asset'].address  str.encode(link_approve) uniswap_v3.router.address
routers = [uniswap_v3.router.address, uniswap_v3.router.address, ]
trades = [str.encode(buy_weth_encoded), str.encode(buy_link_encoded)]
tokens = [weth_usdt['quote_asset'].address, link_weth['quote_asset'].address,]
approves = [str.encode(usdt_approve), str.encode(weth_approve),]
print(buy_weth_encoded)
print(buy_link_encoded)
print(routers[0])
print(trades[0])
print(type(uniswap_v3.router.address))
print(type(buy_weth_encoded))

encoded_data = encode(types=['address[]', 'bytes[]', 'address[]', 'bytes[]'],
                      args=[routers, trades, tokens, approves])

print(encoded_data)
encode_addr = encode(types=['address[]', 'bytes[]'],
                        args=[routers, trades])
#print(encode_addr)
# tokens[0], 1000*10**6,

print(uniswap_v3.arbitrage_contract.functions.viewParams(encode_addr).call())

gas_price = uniswap_v3.web3_client.to_wei(40, 'gwei')


my_address = os.environ['address']
my_private_key = os.environ['private_key']

nonce = uniswap_v3.web3_client.eth.get_transaction_count(my_address)

chain_id = uniswap_v3.web3_client.eth.chain_id
max_fee = uniswap_v3.web3_client.to_wei(100, 'gwei')
max_fee_gas = uniswap_v3.web3_client.to_wei(40, 'gwei')
call_function = uniswap_v3.arbitrage_contract.functions.requestFlashLoan(
    tokens[0], 1000*10**6,
    encoded_data).build_transaction({"chainId": chain_id,
                                    "from": my_address, "nonce": nonce, "gas": 6721975,'maxFeePerGas': max_fee,
  'maxPriorityFeePerGas':max_fee_gas})

print(call_function)

signed_tx = uniswap_v3.web3_client.eth.account.sign_transaction(call_function, private_key=my_private_key)

send_tx = uniswap_v3.web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)

tx_receipt = uniswap_v3.web3_client.eth.wait_for_transaction_receipt(send_tx)

print(tx_receipt)





