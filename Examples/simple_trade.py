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
encoded_approve = sushi3.encode_router_approve(token1, 100)
# token to buy obj
token0 = Token("LINK", "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39", 18)
# encode buy order
encoded_buy_order = sushi3.encode_buy_order(token0, token1, 100)
