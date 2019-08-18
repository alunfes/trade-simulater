import numpy as np


class SimAccount:
    def __init__(self):
        self.__initialize_order()
        self.__initialize_holding()

        self.base_margin_rate = 1.2
        self.leverage = 4.0
        self.slip_page = 50
        self.force_loss_cut_rate = 0.5
        self.initial_asset = 15000
        self.order_cancel_delay = 1
        self.ls_penalty = 50

        self.pl_kijun = 0
        self.ls_kijun = 0

        self.total_pl = 0
        self.realized_pl = 0
        self.current_pl = 0
        self.num_trade = 0
        self.num_sell = 0
        self.num_buy = 0
        self.num_win = 0
        self.win_rate = 0
        self.asset = self.initial_asset

        self.dt_log = []
        self.i_log = []
        self.order_log = []
        self.holding_log = []
        self.total_pl_log = []
        self.action_log = []
        self.price_log = []
        self.performance_total_pl_log = []
        self.performance_dt_log = []
        self.pl_stability = 0

        self.start_dt = ''
        self.end_dt = ''

    def __initialize_order(self):
        self.order_side = ''
        self.order_price = 0
        self.order_size = 0
        self.order_i = 0
        self.order_dt = ''
        self.order_ut = 0
        self.order_type = ''  # market / limit
        self.order_cancel = False
        self.order_expire = 0

    def __initialize_holding(self):
        self.holding_side = ''
        self.holding_price = 0
        self.holding_size = 0
        self.holding_i = 0
        self.holding_dt = ''
        self.holding_ut = 0

    def move_to_next(self, i, dt, openp, high, low, close):
        if len(str(self.start_dt)) < 3:
            self.start_dt = dt
        self.__check_loss_cut(i, dt, high, low)
        self.__check_execution(i, dt, openp, high, low)
        self.__check_cancel(i, dt)
        self.__check_pl(i, dt, high, low)
        self.__check_ls(i, dt, high, low)
        if self.holding_side != '':
            self.current_pl = (close - self.holding_price) * self.holding_size if self.holding_side == 'buy' else (self.holding_price - close) * self.holding_size
        else:
            self.current_pl = 0
        self.total_pl = self.realized_pl + self.current_pl
        self.performance_total_pl_log.append(self.total_pl)
        self.performance_dt_log.append(dt)
        self.asset = self.initial_asset + self.total_pl
        self.price_log.append(close)
        # self.__add_log('i:'+str(i), i)

    def last_day_operation(self, i, dt, openp, high, low, close):
        self.__check_loss_cut(i, dt, high, low)
        self.__check_execution(i, dt, openp, high, low)
        self.__check_cancel(i, dt)
        if self.holding_side != '':
            self.realized_pl += (close - self.holding_price) * self.holding_size if self.holding_side == 'buy' else (self.holding_price - close) * self.holding_size
        self.total_pl = self.realized_pl
        self.num_trade += 1
        self.total_pl_log.append(self.total_pl)
        self.performance_total_pl_log.append(self.total_pl)
        self.performance_dt_log.append(dt)
        if self.num_trade > 0:
            self.win_rate = round(float(self.num_win) / float(self.num_trade), 4)
        self.__add_log('Sim Finished.', i, dt)
        self.end_dt = dt
        self.__calc_pl_stability()
        #print('from dt={}, : to_dt={}, total p={}, num trade={}, win rate={}'.format(self.start_dt, self.end_dt,
        #                                                                             self.total_pl, self.num_trade,
        #                                                                             self.win_rate))

    def entry_order(self, side, price, size, type, expire, pl, ls, i, dt):
        if self.order_side == '':
            if side == 'buy':
                self.num_buy += 1
            elif side == 'sell':
                self.num_sell += 1
            self.order_side = side
            self.order_price = price
            self.order_size = size
            self.order_i = i
            self.order_dt = dt
            self.order_type = type  # limit, market
            self.order_cancel = False
            self.order_expire = expire
            self.pl_kijun = pl
            self.ls_kijun = ls
            self.__add_log('entry order' + side + ' type=' + type, i, dt)
        else:
            # print('order is already exist!')
            self.__add_log('order is already exist!', i, dt)

    def __update_holding(self, side, price, size, pl, ls, i, dt):
        self.holding_side = side
        self.holding_price = price
        self.holding_size = size
        self.holding_i = i
        self.holding_dt = dt
        self.pl_kijun = pl
        self.ls_kijun = ls

    def cancel_order(self, i, dt, ut):
        if self.order_type != 'losscut' and self.order_cancel == False:
            self.order_cancel = True
            self.order_i = i
            self.order_dt = dt
            self.order_ut = ut

    def __check_cancel(self, i, dt):
        if self.order_cancel:
            self.__initialize_order()
            self.__add_log('order cancelled.', i, dt)

    def __check_expiration(self, i, dt):
        if i - self.order_i >= self.order_expire and self.order_type == 'limit':
            self.__initialize_order()
            self.__add_log('order expired.', i, dt)

    def __check_pl(self, i, dt, high, low):
        if self.holding_side != '' and self.pl_kijun > 0:
            if self.holding_side == 'buy' and self.holding_price + self.pl_kijun <= high:
                self.__add_log('pl executed.', i, dt)
                self.__calc_executed_pl(self.holding_price + self.pl_kijun, self.holding_size, i)
                self.__initialize_holding()
                # self.__update_holding(self.holding_side, self.holding_price + self.pl_kijun + 100, self.holding_size, self.pl_kijun, self.ls_kijun, True, i, dt, ut)
            if self.holding_side == 'sell' and self.holding_price - self.pl_kijun >= low:
                self.__add_log('pl executed.', i, dt)
                self.__calc_executed_pl(self.holding_price - self.pl_kijun, self.holding_size, i)
                self.__initialize_holding()
                # self.__update_holding(self.holding_side, self.holding_price - self.pl_kijun - 100, self.holding_size, self.pl_kijun, self.ls_kijun, True, i, dt, ut)

    def __check_ls(self, i, dt, ut, tick_price):
        if self.holding_side != '' and self.ls_kijun > 0:
            if self.holding_side == 'buy' and self.holding_price - self.ls_kijun >= tick_price:
                self.__add_log('ls executed.', i, dt, ut, tick_price)
                self.__calc_executed_pl(self.holding_price - self.ls_kijun - self.ls_penalty, self.holding_size, i)
                self.__initialize_holding()
            if self.holding_side == 'sell' and self.holding_price + self.ls_kijun <= tick_price:
                self.__add_log('ls executed.', i, dt, ut, tick_price)
                self.__calc_executed_pl(self.holding_price + self.ls_kijun + self.ls_penalty, self.holding_size, i)
                self.__initialize_holding()

    def __check_execution(self, i, dt, openp, high, low):
        if self.order_side != '' and self.order_i < i:
            if self.order_type == 'market':
                self.__process_execution(openp, i, dt)
                self.__initialize_order()
            elif self.order_type == 'limit' and ((self.order_side == 'buy' and self.order_price >= low) or (
                    self.order_side == 'sell' and self.order_price <= high)):
                self.__process_execution(self.order_price, i, dt)
                self.__initialize_order()
            elif self.order_type != 'market' and self.order_type != 'limit' and self.order_type != 'losscut':
                print('Invalid order type!' + self.order_type)
                self.__add_log('invalid order type!' + self.order_type, i, dt)

    def __process_execution(self, exec_price, i, dt):
        if self.order_side != '':
            if self.holding_side == '':  # no position
                self.__update_holding(self.order_side, exec_price, self.order_size, self.pl_kijun, self.ls_kijun, i, dt)
                self.__add_log('New Entry:' + self.order_type, i, dt)
            else:
                if self.holding_side == self.order_side:  # order side and position side is matched
                    ave_price = round(((self.holding_price * self.holding_size) + (exec_price * self.order_size)) / (self.order_size + self.holding_size))  # averaged holding price
                    self.__update_holding(self.holding_side, ave_price, self.order_size + self.holding_size,self.pl_kijun, self.ls_kijun, i, dt)
                    self.__add_log('Additional Entry:' + self.order_type, i, dt)
                elif self.holding_size > self.order_size:  # side is not matched and holding size > order size
                    self.__calc_executed_pl(exec_price, self.order_size, i)
                    self.__update_holding(self.holding_side, self.holding_price, self.holding_size - self.order_size, self.pl_kijun, self.ls_kijun, i, dt)
                    self.__add_log('Exit Order (h>o):' + self.order_type, i, dt)
                elif self.holding_size == self.order_size:
                    self.__add_log('Exit Order (h=o):' + self.order_type, i, dt)
                    self.__calc_executed_pl(exec_price, self.order_size, i)
                    self.__initialize_holding()
                else:  # in case order size is bigger than holding size
                    self.__calc_executed_pl(exec_price, self.holding_size, i)
                    self.__add_log('Exit & Entry Order (h<o):' + self.holding_side, i, dt)
                    self.__update_holding(self.order_side, exec_price, self.order_size - self.holding_size, self.pl_kijun, self.ls_kijun, i, dt)

    def __calc_executed_pl(self, exec_price, size, i):  # assume all order size was executed
        pl = (exec_price - self.holding_price - self.slip_page) * size if self.holding_side == 'buy' else (self.holding_price - exec_price - self.slip_page) * size
        self.realized_pl += round(pl)
        self.num_trade += 1
        if pl > 0:
            self.num_win += 1

    def __check_loss_cut(self, i, dt, high, low):
        if self.holding_side != '':
            price = high if self.holding_side == 'sell' else low
            req_collateral = self.holding_size * price / self.leverage
            pl = price - self.holding_price if self.holding_side == 'buy' else self.holding_price - price
            pl = pl * self.holding_size
            margin_rate = (self.initial_asset + self.realized_pl + pl) / req_collateral
            if margin_rate <= self.force_loss_cut_rate:
                self.__force_exit(i, dt)
                self.__add_log('Loss cut postion! margin_rate=' + str(margin_rate), i, dt)

    def __force_exit(self, i, dt):
        self.order_side = 'buy' if self.holding_side == 'sell' else 'sell'
        self.order_size = self.holding_size
        self.order_type = 'losscut'
        self.order_i = i
        self.order_dt = dt
        self.order_cancel = False
        self.order_expire = i

    def __calc_pl_stability(self):
        base_line = np.linspace(self.performance_total_pl_log[0], self.performance_total_pl_log[-1],
                                num=len(self.performance_total_pl_log))
        sum_diff = 0
        for i in range(len(base_line)):
            sum_diff += (base_line[i] - self.performance_total_pl_log[i]) ** 2
        self.pl_stability = round(1.0 / ((sum_diff ** 0.5) * self.total_pl / float(len(self.performance_total_pl_log))),
                                  4)

    def __add_log(self, log, i, dt):
        self.total_pl_log.append(self.total_pl)
        self.action_log.append(log)
        self.holding_log.append(self.holding_side + ' @' + str(self.holding_price) + ' x' + str(self.holding_size))
        self.order_log.append(
            self.order_side + ' @' + str(self.order_price) + ' x' + str(self.order_size) + ' cancel=' + str(
                self.order_cancel) + ' type=' + self.order_type)
        self.i_log.append(i)
        self.dt_log.append(dt)
#        print('i={},dt={},action={},holding side={}, holding price={},holding size={},order side={},order price={},order size={},pl={},num_trade={}'.format(i, tick_price,log,self.holding_side,self.holding_price,self.holding_size,self.order_side,self.order_price,self.order_size,self.total_pl,self.num_trade))