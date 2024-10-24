import datetime
import math
import threading
import time
from random import sample

import numpy as np
from numpy.core.records import ndarray

from helper.calculator import *
from helper.wing_model import *
from helper.helper import INDEX_OPTION_PREFIXES, count_trading_days, HOLIDAYS, YEAR_TRADING_DAY, INTEREST_RATE, DIVIDEND
from model.instrument.option import Option
from model.instrument.option_series import OptionSeries


class OptionManager:
    # 期权链
    option_series_dict = dict()

    # 到期时间
    option_expired_date = []

    # 剩余时间
    index_option_remain_year = []

    # 期权品种月份列表
    index_option_month_forward_id = []

    # 期权品种月份行权价数量
    index_option_month_strike_num = []
    index_option_month_strike_prices = {} # ['HO2410':{2400, 2500}]

    # 最多数量的行权价
    index_option_month_strike_max_num = 0


    """
    # 期权行情结构
    第一个维度：品种月份维度，顺序与期权品种月份列表对齐，[0, : , : , : ]代表HO2410
    第二个维度：固定大小为2，看涨or 看跌，看涨期权为0，看跌期权为1
    第三个维度：行权价维度
    第四个维度：字段维度固定大写为7，七个字段存放内容为：行权价，字段时间，bid, bidv, ask, askv, available
    例如要取HO2410的看涨期权的第一个行权价的bid价格，index_option_market_data[0, 0, 0, 2]
    """
    index_option_market_data = ndarray

    index_option_month_atm_volatility = ndarray

    index_option_month_model_para = ndarray

    index_option_month_t_iv = ndarray

    index_option_month_greeks = ndarray

    def __init__(self, index_options):
        self.init_option_series(index_options)
        self.init_index_option_month_id()
        self.init_index_option_expired_date(index_options)
        self.init_index_option_remain_day()
        self.init_index_option_month_strike_num()
        self.init_index_option_market_data()

        #初始化IS相关数组
        self.index_option_month_forward_price = None
        self.init_index_option_month_forward_price()

        self.init_index_option_month_atm_vol()
        self.init_index_option_month_model_para()

        #初始化T型IV相关结构
        self.init_index_option_month_t_iv()
        self.init_index_option_month_greeks()

        self.greeks_lock = threading.Lock()

    def init_option_series(self, options: [Option]):
        """
        根据期权名称分组期权并初始化 OptionSeries。
        :param options: List[Option] - Option 对象的列表
        """
        option_series_dict = {}

        # 按名称分组期权
        for option in options:
            if option.symbol not in option_series_dict:
                option_series_dict[option.symbol] = []
            option_series_dict[option.symbol].append(option)

        # 初始化 OptionSeries
        for name, options_list in option_series_dict.items():
            self.option_series_dict[name] = OptionSeries(name, options_list)



    def init_index_option_month_id(self):
        """
        生成唯一的期权月份列表，格式如：["HO2410","HO2411","HO2412","HO2501","HO2503","HO2506",…,…]
        """

        for name in self.option_series_dict.keys():
            self.index_option_month_forward_id.append(name)

        sorted(self.index_option_month_forward_id)

    def init_index_option_expired_date(self, options: [Option]):
        expired_date = set()
        for option in options:
            expired_date.add(option.expired_date)

        expired_date_list = sorted(list(expired_date))
        for _ in INDEX_OPTION_PREFIXES:
            self.option_expired_date += expired_date_list

    def init_index_option_remain_day(self):
        for date in self.option_expired_date:
            start_date = datetime.datetime.now().date()
            end_date = datetime.datetime.strptime(date, "%Y%m%d").date()
            day_count = count_trading_days(start_date, end_date, HOLIDAYS)
            self.index_option_remain_year.append(round((day_count - 1) / YEAR_TRADING_DAY, 4))


    def init_index_option_month_strike_num(self):
        """
        生成每个期权品种月份对应的行权价数量列表。
        假设期权格式为：'HO2410-C-4100'，表示品种HO，月份2410，行权价4100
        """

        for name in self.index_option_month_forward_id:
            self.index_option_month_strike_num.append(self.option_series_dict[name].get_num_strike_price())

        self.index_option_month_strike_max_num = max(self.index_option_month_strike_num)

    def init_index_option_market_data(self):
        """
        假设有 len(self.index_option_month_forward_id) 个月份，每个期权品种最多有 2 种看涨/看跌期权，index_option_month_strike_max_num 个行权价，每个行权价有 7 个字段
        [1]行权价 [2]字段时间 [3]bid [4]bid_volume [5]ask [6]ask_volume [7]available
        :return: 
        """
        self.index_option_market_data = np.zeros((len(self.index_option_month_forward_id), 2, self.index_option_month_strike_max_num, 7))

        for i, name in enumerate(self.index_option_month_forward_id):
            strike_prices = self.option_series_dict[name].get_all_strike_price()
            for j, strike_price in enumerate(strike_prices):
                self.index_option_market_data[i, 0, j, 0] = strike_price
                self.index_option_market_data[i, 1, j, 0] = strike_price

    def init_index_option_month_forward_price(self):
        """
        # 0（远期有效性），1（远期ask），2（远期bid），3（Askstrike），4（BIDstrike），5（ATMS有效性），6（Ask），7（Bid），8（K1），9（K2），10（K3），11（K4），12（ISask），13（ISbid）
        """
        self.index_option_month_forward_price = np.zeros((len(self.index_option_month_forward_id), 14))

    def init_index_option_month_atm_vol(self):
        """
        [1] 当前ATM有效性 [2] K1 volatility [3] K2 volatility [4] K3 volatility [5] 序列保护的atm volatility [6] atm_gamma [7] atm_vega [8] X-1.98 [9] X-1.32 [10] X-0.66 [11] X0 [12] X+1.98 [13] X+1.32 [14] X+0.66
        """
        self.index_option_month_atm_volatility = np.zeros((len(self.index_option_month_forward_id), 15))

    def init_index_option_month_model_para(self):
        self.index_option_month_model_para = np.zeros((len(self.index_option_month_forward_id), 5))

    def init_index_option_month_t_iv(self):
        """
        [1] 行权价 [2] call ask volatility [3] call bid volatility [4] put ask volatility [5] put bid volatility [6] 样本有效性 [7] X [8] sample volatility [9] 拟合vega
        """
        self.index_option_month_t_iv = np.zeros((len(self.index_option_month_forward_id), self.index_option_month_strike_max_num, 9))
        for i in range(len(self.index_option_month_forward_id)):
            # 行权价
            self.index_option_month_t_iv[i, :, 0] = self.index_option_market_data[i, 0, :, 0].copy()

    def init_index_option_month_greeks(self):
        self.index_option_month_greeks = np.zeros((len(self.index_option_month_forward_id), self.index_option_month_strike_max_num, 14))
        for i in range(len(self.index_option_month_forward_id)):
            # 行权价
            self.index_option_month_greeks[i, :, 0] = self.index_option_market_data[i, 0, :, 0].copy()

    def get_option(self, instrument_id):
        symbol = instrument_id.split('-')[0]
        strike_price = instrument_id.split('-')[-1]
        if instrument_id[7] == "C":
            return self.option_series_dict[symbol][strike_price][0]
        elif instrument_id[7] == "P":
            return self.option_series_dict[symbol][strike_price][1]



    def index_volatility_calculator(self):
        while True:
            timestamp = time.time()
            for i, symbol in enumerate(self.index_option_month_forward_id):
                # 计算forward价格，获取两侧行权价，标记FW价格无效，loc_index_month_available,标记IS无法取得,loc_index_IS_available
                self.index_option_imply_forward_price(i)
                if self.index_option_month_forward_price[i, 0] == -1:
                    self.index_option_month_atm_volatility[i, :] = -1
                    # print(f'{symbol} month tick error')
                    continue
                else:
                    self.calculate_atm_para(i)
                    self.calculate_index_option_month_t_iv(i)
                    self.calculate_wing_model_para(i)

                    with self.greeks_lock:
                        self.calculate_greeks(i)

            time.sleep(2)

    def calculate_greeks(self, index):
        underlying_price = (self.index_option_month_forward_price[index, 12] + self.index_option_month_forward_price[index, 13]) / 2
        strike_prices = self.index_option_market_data[index, 0, :, 0]
        remain_time = self.index_option_remain_year[index]
        volatility = self.index_option_month_atm_volatility[index, 5]
        wing_model = self.index_option_month_model_para[index, 1:4]
        strike_price_num = self.index_option_month_strike_num[index]

        # if index == 1:
        #     j = 10
        #     print(f'underlying_price: {underlying_price}, strike_price: {strike_prices[j]}, remain_time: {remain_time}, volatility: {volatility}, wing model: {wing_model}')
        self.index_option_month_greeks[index, 0:strike_price_num, 1] = v_delta('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 2] = v_delta('p', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 3] = v_gamma_percent('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 4] = v_vega('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 5] = v_theta('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 6] = v_theta('p', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 7] = v_vannasv('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 8] = v_vannasv('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 9] = v_db('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 10] = v_vomma('p', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 11] = v_dk1('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 12] = v_dk2('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])
        self.index_option_month_greeks[index, 0:strike_price_num, 13] = v_charm('c', underlying_price, strike_prices[0:strike_price_num], remain_time, INTEREST_RATE, volatility, DIVIDEND, wing_model[0], wing_model[1], wing_model[2])


    def calculate_wing_model_para(self, index):
        underlying_price = (self.index_option_month_forward_price[index, 12] + self.index_option_month_forward_price[index, 13]) / 2
        strike_prices = self.index_option_market_data[index, 0, :, 0]
        remain_time = self.index_option_remain_year[index]
        volatility = self.index_option_month_atm_volatility[index, 5]
        sample_volatility = self.index_option_month_t_iv[index, :, 7]
        sample_available = self.index_option_month_t_iv[index, :, 5]
        strike_price_num = self.index_option_month_strike_num[index]

        available_num = np.count_nonzero(sample_available)
        if available_num <= 3:
            self.index_option_month_model_para[index, 0:6] = [underlying_price, 0, 0, 0, -1]
            return

        # 剔除掉
        cut_point = 2
        x_array = np.zeros((strike_price_num, 3))
        y_array = np.zeros(strike_price_num)
        for j in range(strike_price_num):
            x_distance = calculate_x_distance(S=underlying_price, K=strike_prices[j], t=remain_time, r=INTEREST_RATE, v=volatility, q=DIVIDEND)
            if -cut_point < x_distance <= 0:
                x_array[j, 0] = x_distance * x_distance * sample_available[j]
                x_array[j, 2] = x_distance * sample_available[j]
                y_array[j] = (sample_volatility[j] - volatility) * sample_available[j]
            elif 0 < x_distance <= cut_point:
                x_array[j, 1] = x_distance * x_distance * sample_available[j]
                x_array[j, 2] = x_distance * sample_available[j]
                y_array[j] = (sample_volatility[j] - volatility) * sample_available[j]

        # 参数估计
        para_array = np.dot(np.dot(np.linalg.inv(np.dot(np.transpose(x_array), x_array)), np.transpose(x_array)),y_array)
        # 残差序列
        residual = y_array - x_array @ para_array

        self.index_option_month_model_para[index, 0] = underlying_price
        self.index_option_month_model_para[index, 1:4] = para_array
        self.index_option_month_model_para[index, 4] = (residual@residual) / available_num


    def calculate_atm_para(self, index):
        # K1 左二 K2 左一 K3 右一 k4 右二
        [k1_strike, k2_strike, k3_strike, k4_strike] = self.index_option_month_forward_price[index, 8:12]
        # if index == 1:
        #     print(f"k1:{k1_strike}, k2:{k2_strike}, k3:{k3_strike}, k4:{k4_strike}")
        strike_prices = self.index_option_market_data[index, 0, :, 0]
        # option ask bid 取中间价
        call_price = (self.index_option_market_data[index, 0, :, 4] + self.index_option_market_data[index, 0, :, 2]) / 2
        put_price = (self.index_option_market_data[index, 1, :, 4] + self.index_option_market_data[index, 1, :, 2]) / 2
        remain_time = self.index_option_remain_year[index]
        # 对应标的物的远期价格
        underlying_price = (self.index_option_month_forward_price[index, 12] + self.index_option_month_forward_price[index, 13]) / 2

        forward_underlying_price = underlying_price * math.exp(remain_time * (INTEREST_RATE - DIVIDEND))

        # 判断离平值期权最近的
        if k2_strike == -1 or k3_strike == -1:
            self.index_option_month_atm_volatility[index, 0] = -1
            self.index_option_month_atm_volatility[index, 1:5] = -1
        else:
            k2_strike_index = list(strike_prices).index(k2_strike)
            k3_strike_index = k2_strike_index + 1
            # if index == 1:
            #     print(f"calculate_imply_volatility: underlying price:{underlying_price}, k2:{k2_strike}, remain_time:{remain_time}, call_price:{call_price[k2_strike_index]}")
            k2_call_volatility = calculate_imply_volatility('c', underlying_price, k2_strike, remain_time, INTEREST_RATE, call_price[k2_strike_index], DIVIDEND)
            k2_put_volatility = calculate_imply_volatility('p', underlying_price, k2_strike, remain_time, INTEREST_RATE, put_price[k2_strike_index], DIVIDEND)
            k3_call_volatility = calculate_imply_volatility('c', underlying_price, k3_strike, remain_time, INTEREST_RATE, call_price[k3_strike_index],DIVIDEND)
            k3_put_volatility = calculate_imply_volatility('p', underlying_price, k3_strike, remain_time, INTEREST_RATE, put_price[k3_strike_index],DIVIDEND)

            # 对于K1 K4 行权价只计算call 或者 put
            k1_strike_index = k2_strike_index - 1
            k4_strike_index = k3_strike_index + 1
            k1_put_volatility = calculate_imply_volatility('p', underlying_price, k1_strike, remain_time, INTEREST_RATE, put_price[k1_strike_index],DIVIDEND)
            k4_call_volatility = calculate_imply_volatility('c', underlying_price, k4_strike, remain_time, INTEREST_RATE, call_price[k4_strike_index],DIVIDEND)

            volatility = [k1_put_volatility, (k2_call_volatility + k2_put_volatility) / 2, (k3_call_volatility + k3_put_volatility) / 2, k4_call_volatility]

            # if index == 1:
            #     print(f"volatility{volatility}")

            # 左右行权价计算的波动率无效
            if k2_call_volatility == -1 or k2_put_volatility == -1 or k3_call_volatility == -1 or k3_put_volatility == -1:
                self.index_option_month_atm_volatility[index, 0] = -1
                self.index_option_month_atm_volatility[index, 1:5] = -1
            else:
                self.index_option_month_atm_volatility[index, 0] = 1
                self.index_option_month_atm_volatility[index, 1:5] = volatility
                if k1_put_volatility != -1 and k4_call_volatility == -1:
                    # 左中有效 右无效
                    self.index_option_month_atm_volatility[index, 5] = estimate_atm_volatility(np.array([k1_strike, k2_strike, k3_strike]), np.array(volatility[0:3]), forward_underlying_price)
                if k1_put_volatility == -1 and k4_call_volatility != -1:
                    # 左无效 右中有效
                    self.index_option_month_atm_volatility[index, 5] = estimate_atm_volatility(np.array([k2_strike, k3_strike, k4_strike]), np.array(volatility[1:]), forward_underlying_price)
                if k1_put_volatility != -1 and k4_call_volatility != -1:
                    # 全部有效
                    self.index_option_month_atm_volatility[index, 5] = (estimate_atm_volatility(np.array([k1_strike, k2_strike, k3_strike]), np.array(volatility[0:3]), forward_underlying_price) + estimate_atm_volatility(np.array([k2_strike, k3_strike, k4_strike]), np.array(volatility[1:]), forward_underlying_price)) / 2
                # if left2_put_volatility == -1 and right2_call_volatility == -1:
                #     # 仅中间有效
                #     self.index_option_month_atm_volatility[index, 5] = self.index_option_month_atm_volatility[index, 5]

        # 如果波动率自始至终都是0或者-1，则平值波动率参数全为-1
        if self.index_option_month_atm_volatility[index, 5] > 0:
            self.index_option_month_atm_volatility[index, 6] = calculate_gamma('c', underlying_price, forward_underlying_price, remain_time, INTEREST_RATE, self.index_option_month_atm_volatility[index, 5], DIVIDEND)
            self.index_option_month_atm_volatility[index, 7] = calculate_gamma('c', underlying_price, forward_underlying_price, remain_time, INTEREST_RATE, self.index_option_month_atm_volatility[index, 5], DIVIDEND)
            for j in range(7):
                self.index_option_month_atm_volatility[index, 8+j] = math.exp((j * 0.66 - 1.98) * self.index_option_month_atm_volatility[index, 5] * math.sqrt(remain_time)) * forward_underlying_price

        # if index == 1:
        #     print(f"index_option_month_atm_volatility:{self.index_option_month_atm_volatility[index]}")

    def calculate_index_option_month_t_iv(self, index):
        strike_price_num = self.index_option_month_strike_num[index]

        call_bid_price = self.index_option_market_data[index, 0, :, 4]
        call_ask_price = self.index_option_market_data[index, 0, :, 2]
        put_bid_price = self.index_option_market_data[index, 1, :, 4]
        put_ask_price = self.index_option_market_data[index, 1, :, 2]
        # 对应标的物的远期价格
        underlying_price = (self.index_option_month_forward_price[index, 12] + self.index_option_month_forward_price[index, 13]) / 2
        remain_time = self.index_option_remain_year[index]
        volatility =  self.index_option_month_atm_volatility[index, 5]
        call_available =  self.index_option_market_data[index, 0, :, 6]
        put_available = self.index_option_market_data[index, 1, :, 6]

        for j in range(strike_price_num):
            self.index_option_month_t_iv[index, j, 1] = calculate_imply_volatility('c', underlying_price, self.index_option_month_t_iv[index, j, 0], remain_time, INTEREST_RATE, call_ask_price[j], DIVIDEND)
            self.index_option_month_t_iv[index, j, 2] = calculate_imply_volatility('c', underlying_price, self.index_option_month_t_iv[index, j, 0], remain_time, INTEREST_RATE, call_bid_price[j], DIVIDEND)
            self.index_option_month_t_iv[index, j, 3] = calculate_imply_volatility('p', underlying_price, self.index_option_month_t_iv[index, j, 0], remain_time, INTEREST_RATE, put_ask_price[j], DIVIDEND)
            self.index_option_month_t_iv[index, j, 4] = calculate_imply_volatility('p', underlying_price, self.index_option_month_t_iv[index, j, 0], remain_time, INTEREST_RATE, put_bid_price[j], DIVIDEND)

        if volatility > 0:
            sample_delta = calculate_delta('c', underlying_price, self.index_option_month_t_iv[index, 0:strike_price_num, 0], remain_time, INTEREST_RATE, volatility, DIVIDEND)
            available_put_volatility = call_available * self.index_option_month_t_iv[index, :, 4] > 0
            available_call_volatility = put_available * self.index_option_month_t_iv[index, :, 2] > 0
            for j in range(strike_price_num):
                # 样本有效性
                self.index_option_month_t_iv[index, j, 6] = calculate_x_distance(underlying_price, self.index_option_month_t_iv[index, j, 0], remain_time, INTEREST_RATE, volatility, DIVIDEND)
                # 偏离一个标准差的距离，call 没有参考价值
                if self.index_option_month_t_iv[index, j, 6] < -1.32:
                    self.index_option_month_t_iv[index, j, 5] = int(available_put_volatility[j]) if int(available_put_volatility[j]) == 1 else 0
                    if int(available_put_volatility[j]) > 0:
                        self.index_option_month_t_iv[index, j, 7] = (self.index_option_month_t_iv[index, j, 4] + self.index_option_month_t_iv[index, j, 3]) / 2
                # 偏离一个标准差的距离，put 没有参考价值
                elif self.index_option_month_t_iv[index, j, 6] > 1.32:
                    self.index_option_month_t_iv[index, j, 5] = int(available_call_volatility[j]) if int(available_put_volatility[j]) == 1 else 0
                    if int(available_put_volatility[j]) > 0:
                        self.index_option_month_t_iv[index, j, 7] = (self.index_option_month_t_iv[index, j, 2] + self.index_option_month_t_iv[index, j, 1]) / 2
                else:
                    self.index_option_month_t_iv[index, j, 5] = int(available_call_volatility[j] * available_put_volatility[j]) if int(available_call_volatility[j] * available_put_volatility[j]) == 1 else 0
                    if int(available_call_volatility[j] * available_put_volatility[j]) > 0:
                        self.index_option_month_t_iv[index, j, 7] = (((self.index_option_month_t_iv[index, j, 2] + self.index_option_month_t_iv[index, j, 1]) / 2) * (1 - sample_delta[j]) +
                                                                     ((self.index_option_month_t_iv[index, j, 4] + self.index_option_month_t_iv[index, j, 3]) / 2) * sample_delta[j])
        # if index == 1:
        #     print(self.index_option_month_t_iv[index, 20])



    def index_option_imply_forward_price(self, index):
        """
        计算一个symbol期权下所有的隐含波动率
        [0]（远期有效性） [1] 远期 ask [2] 远期 bid [3] ask strike [4] bid strike [5]（ATMS有效性），[6] atm ask [7] atm bid [8]（K1 平值左侧第二行权价），9（K2 平值左侧行权价），10（K3 平值右侧行权价），11（K4 平值右侧第二行权价），12（ISask），13（ISbid）
        @para
        """
        call_available = self.index_option_market_data[index, 0, :, 6]
        put_available = self.index_option_market_data[index, 1, :, 6]
        strike_prices = self.index_option_market_data[index, 0, :, 0]
        call_ask1_price = self.index_option_market_data[index, 0, :, 4]
        call_bid1_price = self.index_option_market_data[index, 0, :, 2]
        put_ask1_price = self.index_option_market_data[index, 1, :, 4]
        put_bid1_price = self.index_option_market_data[index, 1, :, 2]
        remain_time = self.index_option_remain_year[index]
        num_strike_price = self.option_series_dict[self.index_option_month_forward_id[index]].get_num_strike_price()

        # 检查是否有至少一组看涨和看跌期权可以交易
        # 至少有一组C与P必须同时可交易才能生成forward，否则返回-1
        trading_pairs = call_available * put_available
        if 1 in trading_pairs:
            self.index_option_month_forward_price[index, 0] =1

            tradable_indices = trading_pairs != 0

            # 计算ask数组和bid数组
            forward_ask_prices = calculate_prices(call_ask1_price[tradable_indices], put_bid1_price[tradable_indices], strike_prices[tradable_indices], remain_time)
            forward_bid_prices = calculate_prices(call_bid1_price[tradable_indices], put_ask1_price[tradable_indices], strike_prices[tradable_indices], remain_time)

            # 最小ask值及其对应的执行价
            self.index_option_month_forward_price[index, 1] = min(forward_ask_prices)
            self.index_option_month_forward_price[index, 3] = strike_prices[tradable_indices][forward_ask_prices.argmin()]

            self.index_option_month_forward_price[index, 2] = max(forward_bid_prices)
            self.index_option_month_forward_price[index, 4] = strike_prices[tradable_indices][forward_bid_prices.argmax()]

            forward_price = (self.index_option_month_forward_price[index, 1] + self.index_option_month_forward_price[index, 2]) / 2 * math.exp(remain_time * (INTEREST_RATE - DIVIDEND))

            # 查找ATM（平值期权）位置
            atm_location = [-1, -1]
            for j, strike in enumerate(strike_prices):
                if forward_price < strike:
                    atm_location = [j - 1, j]
                    break

            # 如果没有找到有效的ATM位置
            if -1 in atm_location:
                self.index_option_month_forward_price[index, 5:12] = [-1] * 7
                self.index_option_month_forward_price[index, 12:14] = [self.index_option_month_forward_price[index, 1], self.index_option_month_forward_price[index, 2]]
            else:
                # 检查两侧ATM期权的有效性
                is_left_tradable = call_available[atm_location[0]] * put_available[atm_location[0]] == 1
                is_right_tradable = call_available[atm_location[1]] * put_available[atm_location[1]] == 1

                if is_left_tradable and is_right_tradable:
                    self.index_option_month_forward_price[index, 5] = 1

                    # 左侧和右侧的ask和bid价格
                    left_ask = calculate_prices(call_ask1_price[atm_location[0]], put_bid1_price[atm_location[0]], strike_prices[atm_location[0]], remain_time)
                    left_bid = calculate_prices(call_bid1_price[atm_location[0]], put_ask1_price[atm_location[0]], strike_prices[atm_location[0]], remain_time)
                    right_ask = calculate_prices(call_ask1_price[atm_location[1]], put_bid1_price[atm_location[1]], strike_prices[atm_location[1]], remain_time)
                    right_bid = calculate_prices(call_bid1_price[atm_location[1]], put_ask1_price[atm_location[1]], strike_prices[atm_location[1]], remain_time)

                    # 插值计算ask和bid价格
                    strike_diff = strike_prices[atm_location[1]] - strike_prices[atm_location[0]]
                    forward_diff = forward_price - strike_prices[atm_location[0]]

                    self.index_option_month_forward_price[index, 6] = (strike_prices[atm_location[1]] - forward_price) / strike_diff * left_ask + forward_diff / strike_diff * right_ask
                    self.index_option_month_forward_price[index, 7] = (strike_prices[atm_location[1]] - forward_price) / strike_diff * left_bid + forward_diff / strike_diff * right_bid

                    self.index_option_month_forward_price[index, 9] = strike_prices[atm_location[0]]
                    self.index_option_month_forward_price[index, 10] = strike_prices[atm_location[1]]

                    self.index_option_month_forward_price[index, 12:14] = [self.index_option_month_forward_price[index, 6], self.index_option_month_forward_price[index, 7]]
                else:
                    self.index_option_month_forward_price[index, 5:12] = [-1] * 7
                    # 如果atm算不出来 那就只能拿远期的bid ask
                    self.index_option_month_forward_price[index, 12:14] = [self.index_option_month_forward_price[index, 1], self.index_option_month_forward_price[index, 2]]

            # 检查两侧的额外执行价是否有效
            if self.index_option_month_forward_price[index, 9] == -1 or self.index_option_month_forward_price[index, 10] == -1:
                self.index_option_month_forward_price[index, 8] = self.index_option_month_forward_price[index, 11] = -1
            else:
                self.index_option_month_forward_price[index, 8] = strike_prices[atm_location[0] - 1] if atm_location[0] > 0 and trading_pairs[atm_location[0] - 1] == 1 else -1
                self.index_option_month_forward_price[index, 11] = strike_prices[atm_location[1] + 1] if atm_location[1] < len(strike_prices) - 1 and trading_pairs[atm_location[1] + 1] == 1 else -1
            # if index == 0:
            #     print(f"strike_price: {strike_prices}")
            #     print(f"atm location: {atm_location[0]}, {atm_location[1]}")
            #     print(f"trading_pairs: {trading_pairs[atm_location[0] - 1]}")
        else:
            self.index_option_month_forward_price[index] = [-1] * 14

        # if index == 0:
        #     print(self.index_option_month_forward_price[index])