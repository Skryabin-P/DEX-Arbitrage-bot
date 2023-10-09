from BaseExchange import BaseExchange
from BaseToken import BaseToken
from utils import get_contract


class UniswapExchange(BaseExchange):
    def __init__(self, network, fee=None):
        super().__init__(network, fee)
        self._weth_addr = None

    @property
    def quoter_contract(self):
        return get_contract(self.web3_client, abi_name='Uniswap-v3/Quoter')

    @property
    def weth_addr(self):
        if self._weth_addr is None:
            self._weth_addr = self.quoter_contract.functions.WETH9().call()
        return self._weth_addr

    def _get_sell_price(self, base_asset: BaseToken, quote_asset: BaseToken, amount: int):
        converted_amount = amount * 10 ** base_asset.decimals
        sell_price = self.quoter_contract.functions.quoteExactInputSingle(
            base_asset.address, quote_asset.address, self.fee, converted_amount, 0).call() / amount
        return sell_price / 10 ** quote_asset.decimals

    def _get_buy_price(self, base_asset: BaseToken, quote_asset: BaseToken, amount):
        converted_amount = amount * 10 ** base_asset.decimals
        buy_price = self.quoter_contract.functions.quoteExactOutputSingle(
            quote_asset.address, base_asset.address, self.fee, converted_amount, 0).call()
        return buy_price / 10 ** quote_asset.decimals


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    network = os.environ['INFURA_MAINNET']
    Uniswap = UniswapExchange(network)
    # Uniswap.web3_client.eth.contract()
    # factory = get_contract(Uniswap.web3_client, abi_name='Uniswap-v3/Factory')
    # print(factory.functions.tokenCount().call())
    # link_token = BaseToken(address='0x514910771AF9Ca656af840dff83E8264EcF986CA', name='Chainlink',
    #                        symbol='LINK', decimals=18)
    weth = BaseToken(address=Uniswap.weth_addr, name='WETH', symbol='WETH', decimals=18)
    usdt_token = BaseToken(address='0xdAC17F958D2ee523a2206206994597C13D831ec7', name='Tether',
                           symbol='USDT', decimals=6)
    sell_price = Uniswap._get_sell_price(weth, usdt_token, 1)
    print(sell_price)
    buy_price = Uniswap._get_buy_price(weth, usdt_token, 1)
    print(buy_price)

    Uniswap.get_token('0x514910771AF9Ca656af840dff83E8264EcF986CA')

