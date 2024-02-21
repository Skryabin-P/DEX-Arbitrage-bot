# import all necessary libraries
from DEX.SushiSwapV3 import SushiSwapV3
from DEX.Token import Token
from dotenv import load_dotenv
import os
# load environment variables
load_dotenv()
web3_provider = os.environ["INFURA_POLYGON"]
wallet_address = os.environ["WALLET_ADDRESS"]
private_key = os.environ["PRIVATE_KEY"]
# create SushiSwap v3 exchange instance
sushi3 = SushiSwapV3("Polygon", "MAINNET", web3_provider, 500)
# token to sell
token_in = Token("USDC.e", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", 6)
# token to buy
token_out = Token("LINK", "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39", 18)
# get chain_id, if you know it just can pass a number instead
chain_id = sushi3.web3_client.eth.chain_id
# get current transaction count for your wallet
nonce = sushi3.web3_client.eth.get_transaction_count(wallet_address)
# get current gas price
gas_price = sushi3.web3_client.eth.gas_price
# Set maxFeePerGas
max_fee_per_gas = int(gas_price * 1.2)
# Set Miners Fee
max_priority_fee_per_gas = int(gas_price * 0.3)
# create tx_params dict
tx_params = {"chainId": chain_id,
             "from": wallet_address, "gas": 50_000, "nonce": nonce,
             'maxFeePerGas': max_fee_per_gas,
             'maxPriorityFeePerGas': max_priority_fee_per_gas}
amount_in = 100
# approve 100 USDC.e for the router contract
approval_transaction_hash = sushi3.get_router_approval(token_in, amount_in,
                                                       tx_params, private_key)
print(approval_transaction_hash)
# market order with maximum possible slippage, so it won't be reverted
amount_out = 0
slippage = 1
address_to = wallet_address
# tx params for trade transaction
tx_params = {"chainId": chain_id,
             "from": wallet_address, "gas": 250_000, "nonce": nonce+1,
             'maxFeePerGas': max_fee_per_gas,
             'maxPriorityFeePerGas': max_priority_fee_per_gas}
# make a trade
trade_transaction_hash = sushi3.make_trade(token_in, token_out, wallet_address, amount_in,
                                           amount_out, slippage, tx_params, private_key)
print(trade_transaction_hash)
