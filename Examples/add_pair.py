# Import the libraries
from DEX.UniswapV3 import UniswapV3
from DEX.Token import Token
from dotenv import load_dotenv
import os
# load .env file
load_dotenv()
# get our http/https url for rpc node from environment variable
web3_provider = os.environ["INFURA_POLYGON"]
# Create an instance of the UniswapV3 class
pairs = ["WMATIC-WETH", "WMATIC-USDC"]
fee = 500
uniswap_v3 = UniswapV3("Polygon", "MAINNET", web3_provider, fee, pairs)
# create your token objects
token0 = Token(symbol="myToken", address="0xF0245F6251Bef9447A08766b9DA2B07b28aD80B0", decimals=18)
token1 = Token("secondToken", "0x60e274B09F701107A4b3226fCC1376eBDa3cdd92", 6)
# add your new pair to a pair_list
uniswap_v3.add_pair(token0, token1)
print(uniswap_v3.pair_list)
