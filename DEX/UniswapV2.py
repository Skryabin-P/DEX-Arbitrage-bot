import time
from web3._utils.abi import get_abi_output_types
from BaseExchange import BaseExchange
from BaseToken import BaseToken
from utils import get_contract, exec_time
import requests


class UniswapV2(BaseExchange):
    def __init__(self, network, fee=None):
        super().__init__(network, fee)
        self._weth_addr = None
        self._router = None

    @property
    def router(self):
        if self._router is None:
            self._router = get_contract(self.web3_client, abi_name='Uniswap-v2/Router02')
        return self._router

    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.router.functions.WETH().call()
        return self._weth_addr

    def _encode_sell_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: float = 1):
        """
        returns encoded  sell function for pushing to milticall contract
        """
        converted_amount = amount * 10 ** base_asset.decimals
        route = [base_asset.address, quote_asset.address, ]
        return self.router.encodeABI(fn_name='getAmountsOut',
                                     args=(converted_amount, route))

    def _encode_buy_price_func(self, base_asset: BaseToken, quote_asset: BaseToken, amount: float = 1):
        """
        returns encoded  buy function for pushing to milticall contract
        """
        converted_amount = amount * 10 ** base_asset.decimals
        route = [quote_asset.address, base_asset.address]
        # print(self.router.functions.getAmountsIn(converted_amount, route).call()[0] / 10 ** quote_asset.decimals)
        return self.router.encodeABI(fn_name='getAmountsIn',
                                     args=(converted_amount, route))


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    net = os.environ['INFURA_MAINNET']
    client = UniswapV2(net)
    base_asset = BaseToken(name="WETH", address=client.weth_addr, decimals=18)
    quote_asset = BaseToken(name="USDT", address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
                            decimals=6)

    client._encode_sell_price_func(base_asset, quote_asset)
    client._encode_buy_price_func(base_asset, quote_asset)
