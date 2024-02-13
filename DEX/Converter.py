import requests
from numbers import Real


class Converter:
    """
    Converts quote asset amount to other assets amount
    based on quotes from Binance API
    """

    def __init__(self, quote_asset: str, quote_amount: Real):
        self._symbols = None
        self.symbols = ['ETHUSDC', 'ETHUSDT', 'ETHDAI', 'USDCUSDT', 'USDTDAI',
                        'MATICUSDC', 'MATICETH', 'MATICUSDT']
        self.quote_asset = quote_asset
        self.quote_amount = quote_amount
        self.coin_list = ['ETH', 'USDC', 'DAI', 'USDT', 'MATIC', 'USDC.E']

    @property
    def symbols(self):
        return self._symbols

    @symbols.setter
    def symbols(self, symbols):
        if not isinstance(symbols, list):
            raise ValueError(f'Symbols must be a list, got {symbols} instead')
        pairs = []
        for symbol in symbols:
            pairs.append(f'"{symbol}"')
        self._symbols = ','.join(pairs)

    @property
    def quote_amount(self):
        return self._quote_amount

    @quote_amount.setter
    def quote_amount(self, amount: Real):
        if not isinstance(amount, Real):
            raise ValueError('Quote amount must be a real number!')
        if amount <= 0:
            raise ValueError('Quote number must be positive!')
        self._quote_amount = amount

    @property
    def quote_asset(self):
        return self._quote_asset

    @quote_asset.setter
    def quote_asset(self, asset: str):
        if not isinstance(asset, str):
            raise ValueError('Quote asset must be a string!')
        if asset not in self.symbols:
            raise ValueError(f'Quote asset must be in '
                             f'one of the following pairs {self.symbols} \n'
                             f'Got {asset} instead')

        self._quote_asset = asset

    def get_prices(self):
        url = f'https://api-gcp.binance.com/api/v3/' \
              f'ticker/price'
        params = {"symbols": f'[{self.symbols}]'}
        raw_response = requests.get(url, params=params).json()
        prices = {}
        for symbol in raw_response:
            prices[self._convert_binance_symbol_format(
                symbol['symbol'])] = float(symbol['price'])

        # calculate approximate price USDC-DAI from USDT-DAI and USDC-USDT
        self.matic_price = prices['MATIC-USDC']
        prices['USDC-DAI'] = prices['USDT-DAI'] / prices['USDC-USDT']
        prices['MATIC-DAI'] = prices['MATIC-ETH'] * prices['ETH-DAI']
        prices['USDC.E-USDT'] = prices['USDC-USDT']
        prices['USDC-USDC.E'] = 1
        prices['ETH-USDC.E'] = prices['ETH-USDC']
        prices['MATIC-USDC.E'] = prices['MATIC-USDC']
        prices['USDC.E-DAI'] = prices['USDC-DAI']
        revert_prices = {}
        # calculating revert pairs
        for price_key in prices:
            price_key_parts = price_key.split('-')
            revert_prices[f'{price_key_parts[1]}-{price_key_parts[0]}'] = 1 / prices[price_key]
        prices.update(revert_prices)
        return prices

    def _convert_binance_symbol_format(self, symbol: str):
        # Converts Binance COIN1COIN2 format to COIN1-COIN2

        for coin in self.coin_list:
            coin_position = symbol.find(coin)
            if coin_position == 0:
                new_format_symbol = f"{symbol[:(len(coin))]}-{symbol[len(coin):]}"
                return new_format_symbol

    def convert(self):
        converted_amount = {}
        prices = self.get_prices()
        for coin in self.coin_list:
            if coin == self.quote_asset:
                converted_amount[coin] = self.quote_amount
                continue
            converted_price = prices[f'{self.quote_asset}-{coin}'] * self.quote_amount
            coin = 'WETH' if coin == 'ETH' else coin
            coin = 'WMATIC' if coin == 'MATIC' else coin
            converted_amount[coin] = converted_price

        return converted_amount


if __name__ == "__main__":
    converter = Converter('USDC', 100.585)
    print(converter.convert())
