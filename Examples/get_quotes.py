# Import the libraries
from DEX.UniswapV3 import UniswapV3
from DEX.Converter import Converter
from dotenv import load_dotenv
import os
# load .env file
load_dotenv()
# get our http/https url for rpc node from environment variable
web3_provider = os.environ["INFURA_POLYGON"]
# Create an instance of the UniswapV3 class
pairs = ["WMATIC-WETH", "WMATIC-USDC"]
fee = 500
uniswap_v3 = UniswapV3("Polygon", "MAINNET",web3_provider, fee, pairs)

# create Converter object to choose
# in which currency and at what depth to scan the price
# must be on of from ETH, USDT, USDC, MATIC, DAI
converter = Converter('USDT', 100)
# Set or Update quote asset prices in UniswapV3 object
uniswap_v3.quote_asset_prices = converter.convert()
# Get a quote for token pairs ["WMATIC-WETH", "WMATIC-USDC"] on Uniswap V3
uniswap_v3.update_price_book()
# Print the quote
for pair, prices in uniswap_v3.price_book.items():
    print(f'Token Pair: {pair}')
    print('Buy price: ', prices['buy_price'])
    print('Sell price: ', prices['sell_price'])
    print('----------------------------------')