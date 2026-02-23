"""מקליט עקומת equity לאורך הזמן"""

import backtrader as bt


class EquityRecorder(bt.Analyzer):
    """שומר את שווי התיק בכל בר"""

    def __init__(self):
        self.equity_curve = []

    def notify_timer(self, timer, when, *args, **kwargs):
        pass

    def start(self):
        self.equity_curve = []

    def notify_trade(self, trade):
        pass

    def notify_order(self, order):
        pass

    def notify_cashvalue(self, cash, value):
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        pass

    def next(self):
        try:
            dt = self.strategy.datas[0].datetime.date(0)
            val = self.strategy.broker.getvalue()
            self.equity_curve.append((dt, val))
        except Exception:
            pass

    def get_analysis(self):
        return {"equity_curve": self.equity_curve}
