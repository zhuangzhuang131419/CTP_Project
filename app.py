import time
import numpy as np
from numpy.core.defchararray import title

np.set_printoptions(suppress=True)
from threading import Thread

from ctp.ctp_manager import CTPManager
from memory.memory_manager import MemoryManager
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates")

@app.route('/')
def index():
    return render_template('index.html', title='我的前端页面', message='欢迎使用 Flask')


def main():
    # 初始化
    ctp_manager = CTPManager()
    ctp_manager.connect_to_market_data()
    time.sleep(3)

    ctp_manager.connect_to_trader()
    while not ctp_manager.trader_user_spi.login_finish:
        time.sleep(3)

    # 查询合约
    ctp_manager.query_instrument()
    while not ctp_manager.trader_user_spi.query_finish:
        time.sleep(3)

    instrument_ids = list(ctp_manager.trader_user_spi.exchange_id.keys())
    print('当前订阅的合约数量为:{}'.format(len(instrument_ids)))

    # 初始化内存
    ctp_manager.memory = MemoryManager(ctp_manager.trader_user_spi.expire_date)

    # 订阅合约
    ctp_manager.subscribe_market_data_in_batches(instrument_ids)

    print('当前订阅期货合约数量为：{}'.format(len(ctp_manager.memory.future_manager.index_futures)))
    print('当前订阅期权合约数量为：{}'.format(len(ctp_manager.memory.option_manager.option_series_dict)))
    print('当前订阅期货合约月份为：{}'.format(ctp_manager.memory.future_manager.index_future_month_id))
    print('当前订阅期权合约月份为：{}'.format(ctp_manager.memory.option_manager.index_option_month_forward_id))
    print('当前订阅期权合约到期月为：{}'.format(ctp_manager.memory.option_manager.option_expired_date))
    print('当前订阅期权合约剩余天数为：{}'.format(ctp_manager.memory.option_manager.index_option_remain_year))
    print('当前订阅期权合约行权价为：{}'.format(ctp_manager.memory.option_manager.option_series_dict['HO2410'].strike_price_options.keys()))
    print('HO2410的看涨期权的第一个行权价的行权价：{}'.format(ctp_manager.memory.option_manager.index_option_market_data[0, 0, 0, 0]))
    print('HO2410的看涨期权的第二个行权价的行权价：{}'.format(
        ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 0]))
    Thread(target=ctp_manager.tick).start()
    Thread(target=ctp_manager.memory.option_manager.index_volatility_calculator).start()


    # print('HO2410的看涨期权的第一个行权价相关信息：{}'.format(
    #     ctp_manager.memory.option_manager.index_option_market_data[0, 0, 0]))
    # print('HO2410一共有几个行权价: {}'.format(memory_manager.option_manager.option_month_strike_prices['HO2410']))
    # print('当前订阅期权合约行权价数量为：{}'.format(memory_manager.option_manager.option_month_strike_num))



    # 模拟下单
    # ctp_manager.insert_order('IF2412', Direction.BUY_OPEN, 4000, 2)

    # ctp_manager.query_investor_position_detail()

    while True:
        strike_price = ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 0]
        timestamp = ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 1]
        bid_price = ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 2]
        bid_volume = ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 3]
        ask_price = ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 4]
        ask_volume = ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 5]
        print(f'HO2410的看涨期权的第一个行权价相关信息：行权价{strike_price}, 时间{timestamp}, 买一价{bid_price}, 买一量{bid_volume}, 卖一价{ask_price}, 卖一量{ask_volume}')
        print('HO2410 期货价格:{}'.format(ctp_manager.memory.option_manager.index_option_month_forward_price[0, :]))
        time.sleep(10)

if __name__ == "__main__":
    Thread(target=main).start()
    app.run(debug=True)