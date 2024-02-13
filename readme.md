# DEX Library

A small library for interacting with different decentralized exchanges (DEX)
for now based on Uniswap V2 and V3. 
This library provides functionality for obtaining quotes,
trades, and other operations related to decentralized exchanges.

## Features

- Obtain quotes for various tokens on different DEX platforms from different Networks
- Encode trades and approves
- Example scripts demonstrating library usage

## Installation

To use the DEX Library, you need to have Python 3.x installed. After that, follow these steps:

1. Clone the repository:

```
$ git clone https://github.com/skryabin-p/dex-library.git
```

2. Install the required dependencies:

```
$ pip install -r requirements.txt
```

## Usage

The DEX Library provides a convenient way to interact with decentralized exchanges. Below are two examples demonstrating how to use the library:

1. Example 1: Getting Quotes

```python
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
```
It will output something like this: 
```
Token Pair: WMATIC-WETH
Buy price:  0.00032822844442613203
Sell price:  0.0003278979643189266
----------------------------------
Token Pair: WMATIC-USDC
Buy price:  0.8765809258858063
Sell price:  0.8756930724042549
----------------------------------
```


2. Example 2: Add custom token pair.

   #### I webscrape to add as many token for different networks as I can.

   But If one or both token not found when you try to set `pair_list`

    you can manually add it to `pair_list` property by this code
```python
# Import the libraries
from DEX.UniswapV3 import UniswapV3
from DEX.BaseToken import BaseToken
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
token0 = BaseToken(symbol="myToken", address="0xF0245F6251Bef9447A08766b9DA2B07b28aD80B0",
                   decimals=18)
token1 = BaseToken("secondToken", "0x60e274B09F701107A4b3226fCC1376eBDa3cdd92", 6)
uniswap_v3.add_pair(token0, token1)
```

3. Example of arbitrage scanner you can see in Examples folder

   To run this script create `.env` file and add enviroment variable `INFURA_POLYGON`
   
   Get free rpc url for polygon network on https://infura.io

   Then run 2 commands 
```
$ cd Examples
$ python AdvancedScanner.py
```
   it will output something like this 
   ```
   +----------------------------------------------------------------------------------------------------------------------------------------+----------------------+
|                                                                  PATH                                                                  |       Profit %       |
+----------------------------------------------------------------------------------------------------------------------------------------+----------------------+
|                                      UniswapV3/3000_WETH-USDC_buy -> UniswapV3/500_WETH-USDC_sell                                      | -0.07486726010091614 |
|                                   UniswapV3/500_WMATIC-WETH_buy -> SushiSwapV3/500_WMATIC-WETH_sell                                    | -0.07995372306155978 |
|                                      UniswapV3/500_WBTC-WETH_buy -> UniswapV3/3000_WBTC-WETH_sell                                      | -0.09740600320688693 |
|                                    UniswapV3/3000_WMATIC-USDC_buy -> UniswapV3/500_WMATIC-USDC_sell                                    | -0.12671511452076345 |
|                                       UniswapV3/500_WBTC-WETH_buy -> SushiSwapV2_WBTC-WETH_sell                                        | -0.13781119865782174 |
|                   UniswapV3/3000_WMATIC-USDC_buy -> SushiSwapV3/500_WMATIC-WETH_sell -> UniswapV3/500_WETH-USDC_sell                   | -0.1393331735394696  |
|   UniswapV3/500_WMATIC-WETH_buy -> SushiSwapV3/500_WMATIC-WETH_sell -> UniswapV3/500_WETH-USDC_sell -> UniswapV3/3000_WETH-USDC_buy    | -0.15476112400066586 |
|      UniswapV3/500_WBTC-WETH_buy -> UniswapV3/3000_WBTC-WETH_sell -> UniswapV3/500_WETH-USDC_sell -> UniswapV3/3000_WETH-USDC_buy      | -0.1722003381020169  |
|   UniswapV3/500_WBTC-WETH_buy -> UniswapV3/3000_WBTC-WETH_sell -> UniswapV3/500_WMATIC-WETH_buy -> SushiSwapV3/500_WMATIC-WETH_sell    | -0.17728184654240603 |
|    UniswapV3/3000_WMATIC-USDC_buy -> UniswapV3/500_WMATIC-USDC_sell -> UniswapV3/3000_WETH-USDC_buy -> UniswapV3/500_WETH-USDC_sell    | -0.20148750648729674 |
|       UniswapV3/500_WBTC-WETH_buy -> SushiSwapV2_WBTC-WETH_sell -> UniswapV3/500_WETH-USDC_sell -> UniswapV3/3000_WETH-USDC_buy        | -0.21257528329019756 |
|                                    UniswapV3/3000_WMATIC-WETH_sell -> UniswapV3/500_WMATIC-WETH_buy                                    | -0.21269955118452727 |
|                                      UniswapV3/500_LINK-WETH_buy -> UniswapV3/3000_LINK-WETH_sell                                      | -0.21471534247310492 |
|     UniswapV3/500_WBTC-WETH_buy -> SushiSwapV2_WBTC-WETH_sell -> UniswapV3/500_WMATIC-WETH_buy -> SushiSwapV3/500_WMATIC-WETH_sell     | -0.21765473653527304 |
|                                   UniswapV3/500_WMATIC-WETH_sell -> SushiSwapV3/500_WMATIC-WETH_buy                                    | -0.2341433782961431  |
   ```
   
   

## Contributing

Contributions are welcome! If you want to contribute to this project, feel free to open a pull request.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Contact

If you have any questions or suggestions, feel free to contact me at skryabin.p.n@gmail.com