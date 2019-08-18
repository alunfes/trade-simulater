class Strategy:
    @classmethod
    def ema_gra_trend_follow(cls, df, term, i, ac):
        dd = DecisionData()
        pred_side = ''
        if ac.holding_side == '':
            if df['ema_gra' + str(term)][i] > 0:
                pred_side = 'buy'
            else:
                pred_side = 'sell'
            dd.set_decision(pred_side, 0, cls.__calc_opt_size(df['open'].iloc[i], ac), 'market', False, 10)  # new entry
        elif ac.holding_side == 'buy':
            if df['ema_gra' + str(term)][i] < 0:
                pred_side = 'sell'
            dd.set_decision(pred_side, 0, ac.holding_size + cls.__calc_opt_size(df['open'].iloc[i], ac), 'market', False, 10)  # exit and entry
        elif ac.holding_side == 'sell':
            if df['ema_gra' + str(term)][i] > 0:
                pred_side = 'buy'
            dd.set_decision(pred_side, 0, ac.holding_size + cls.__calc_opt_size(df['open'].iloc[i], ac), 'market', False, 10)  # exit and entry
        return dd

    @classmethod
    def __calc_opt_size(cls, price, ac):
        return 0.01

class DecisionData:
    def __init__(self):
        self.side = ''
        self.size = 0
        self.price = 0
        self.type = 0
        self.cancel = False
        self.expire = 0  # sec

    def set_decision(self, side, price, size, type, cancel, expire):
        self.side = side
        self.price = price
        self.size = size
        self.type = type
        self.cancel = cancel
        self.expire = expire
