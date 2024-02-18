# import all necessary libraries
from DEX.SushiSwapV3 import SushiSwapV3
from DEX.Token import Token
from dotenv import load_dotenv
import os

# load enviroment variables
load_dotenv()
web3_provider = os.environ["INFURA_POLYGON"]
wallet_address = os.environ["WALLET_ADDRESS"]
private_key = os.environ["PRIVATE_KEY"]

# create SushiSwap v3 exchange instance
sushi3 = SushiSwapV3("Polygon", "MAINNET", web3_provider, 500)

# token to sell object
token1 = Token("USDC.e", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", 6)

# encode approve 100 USDC.e for the router contract
amount_in = 10  # 10 Link
encoded_approve = sushi3.encode_router_approval(token1, amount_in)
# token to buy obj
token0 = Token("LINK", "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39", 18)
# encode buy order

amount_out = 0
slippage = 1  # max slippage
address_to = wallet_address
# encode data for make a raw transaction
encoded_buy_order = sushi3.encode_buy_order(token0, token1, amount_in,
                                            amount_out, address_to, slippage)[0]
signed_tx = sushi3.web3_client.eth.sign_transaction(encoded_buy_order)
print(signed_tx)

