from Strategy import Strategy
from OneMinMarketData import OneMinMarketData
from SimAccount import SimAccount
import pandas as pd

class Sim:
    @classmethod
    def sim_ema_gra_trend_follow_opt(cls, df, opt_term, ema_term_list, ac):
        def __check_opt_ema_term(df, start_i, end_i, ema_term_list):
            pl = {}
            for ema_term in ema_term_list:
                sac = SimAccount()
                pl[ema_term] = cls.sim_ema_trend_follow_period(df, ema_term, start_i, end_i, sac).total_pl
            return max(pl.values()), max(pl, key = pl.get)

        print('sim length:' + str(df['dt'].iloc[0]) + str(df['dt'].iloc[-1]))
        for i in range(opt_term, len(df['dt']) - opt_term -1,1):
            mpl, term = __check_opt_ema_term(df, i-opt_term, i, ema_term_list)
            dd = Strategy.ema_gra_trend_follow(df, term, i, ac)
            if dd.side == '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire,0,0, i, df['dt'].iloc[i])
            ac.move_to_next(i,  df['dt'].iloc[i], df['open'].iloc[i], df['high'].iloc[i], df['low'].iloc[i], df['close'].iloc[i])
        i = len(df['dt']) - opt_term -1
        ac.last_day_operation(i, df['dt'].iloc[i], df['open'].iloc[i], df['high'].iloc[i], df['low'].iloc[i], df['close'].iloc[i])
        return ac

    @classmethod
    def sim_ema_trend_follow_period(cls, df, term, start_i, end_i, ac):
        #print('sim length:' + str(df['dt'].iloc[start_i]) + str(df['dt'].iloc[end_i]))
        for i in range(start_i, end_i, 1):
            dd = Strategy.ema_gra_trend_follow(df, term, i, ac)
            if dd.side != '':
                ac.entry_order(dd.side, dd.price, dd.size, dd.type, dd.expire, 0, 0, i, df['dt'].iloc[i])
            ac.move_to_next(i, df['dt'].iloc[i],df['open'].iloc[i], df['high'].iloc[i], df['low'].iloc[i], df['close'].iloc[i])
        ac.last_day_operation(i, df['dt'].iloc[end_i],df['open'].iloc[end_i], df['high'].iloc[end_i], df['low'].iloc[end_i], df['close'].iloc[end_i])
        return ac



if __name__ == '__main__':
    num_term = 10
    future_side_period = 30
    initial_data_vol = 30000
    OneMinMarketData.initialize_for_bot(num_term, future_side_period, initial_data_vol)
    df = OneMinMarketData.generate_df()
    ac = SimAccount()
    sim = Sim()
    ac = sim.sim_ema_trend_follow_period(df, 500, OneMinMarketData.term_list, ac)
    print('total pl={},num trade={},win rate={}, pl_stability={}, num_buy={}, num_sell={}'.format(ac.total_pl,ac.num_trade,ac.win_rate, ac.pl_stability, ac.num_buy,ac.num_sell))