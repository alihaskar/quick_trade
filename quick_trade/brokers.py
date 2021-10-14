from ccxt import Exchange
from pandas import DataFrame

from . import utils


class TradingClient(object):
    ordered: bool = False
    __side__: str
    ticker: str
    cls_open_orders: int = 0
    base: str
    quote: str
    __quantity__: float

    def __init__(self, client: Exchange):
        self.client = client

    @utils.wait_success
    def order_create(self,
                     side: str,
                     ticker: str = 'None',
                     quantity: float = 0.0):
        utils.logger.info('quantity: %f, side: %s, ticker: %s', quantity, side,
                          ticker)
        if side == 'Buy':
            self.client.create_market_buy_order(symbol=ticker, amount=quantity)
        elif side == 'Sell':
            self.client.create_market_sell_order(symbol=ticker, amount=quantity)
        self.__side__ = side
        self.ticker = ticker
        self.__quantity__ = quantity
        self.base = ticker.split('/')[0]
        self.quote = ticker.split('/')[1]
        self.ordered = True
        self._add_order_count()

    @utils.wait_success
    def get_ticker_price(self,
                         ticker: str) -> float:
        return float(self.client.fetch_ticker(symbol=ticker)['close'])

    def new_order_buy(self,
                      ticker: str = None,
                      quantity: float = 0.0,
                      credit_leverage: float = 1.0):
        self.order_create(side='Buy',
                          ticker=ticker,
                          quantity=quantity * credit_leverage)

    def new_order_sell(self,
                       ticker: str = None,
                       quantity: float = 0.0,
                       credit_leverage: float = 1.0):
        self.order_create(side='Sell',
                          ticker=ticker,
                          quantity=quantity * credit_leverage)

    @utils.wait_success
    def get_data_historical(self,
                            ticker: str = None,
                            interval: str = '1m',
                            limit: int = 1000):

        frames = self.client.fetch_ohlcv(ticker,
                                         interval,
                                         limit=limit)
        data = DataFrame(frames,
                         columns=['time', 'Open', 'High', 'Low', 'Close',
                                  'Volume'])
        return data.astype(float)

    def exit_last_order(self):
        if self.ordered:
            utils.logger.info('client exit')
            bet = self.__quantity__
            if self.__side__ == 'Sell':
                self.new_order_buy(self.ticker,
                                   bet)
            elif self.__side__ == 'Buy':
                self.new_order_sell(self.ticker,
                                    bet)
            self.__side__ = 'Exit'
            self.ordered = False
            self._sub_order_count()

    @utils.wait_success
    def get_balance(self, currency: str) -> float:
        return self.client.fetch_total_balance()[currency]

    @classmethod
    def _add_order_count(cls):
        cls.cls_open_orders += 1
        utils.logger.info('new order')

    @classmethod
    def _sub_order_count(cls):
        cls.cls_open_orders -= 1
        utils.logger.info('order closed')
