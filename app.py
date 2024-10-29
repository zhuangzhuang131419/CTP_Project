import time
import numpy as np

from memory.memory_manager import MemoryManager
from model.ctp_manager import CTPManager
from model.exchange.exchange import Exchange
from model.exchange.exchange_type import ExchangeType
from model.response.option_market_resp import OptionMarketResp, OptionData
from model.response.option_greeks import OptionGreeksData, OptionGreeksResp
from model.response.option_resp_base import StrikePrices
from model.response.user import UserResp
from model.response.wing_model_resp import WingModelResp

np.set_printoptions(suppress=True)
from threading import Thread

from flask import Flask, jsonify, render_template, send_from_directory, request

app = Flask(__name__, static_folder='./frontend/build')

# 路由所有到 React 的前端应用
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and path.startswith('static'):
        # 如果请求的是静态文件，返回对应的静态文件
        return send_from_directory(app.static_folder, path)
    else:
        # 否则返回 React 构建后的 index.html
        return send_from_directory(app.static_folder, 'index.html')

ctp_manager = CTPManager()

def init_ctp():
    # 初始化
    global ctp_manager
    ctp_manager.switch_to_user("test123")


def main():
    future_manager = ctp_manager.current_user.memory.future_manager
    se_option_manager = ctp_manager.current_user.memory.se_option_manager
    cffex_option_manager = ctp_manager.current_user.memory.cffex_option_manager

    if se_option_manager is not None:
        print('当前订阅期权合约数量为：{}'.format(len(ctp_manager.current_user.memory.se_option_manager.option_series_dict)))
        print('当前订阅期权合约到期月为：{}'.format(ctp_manager.current_user.memory.se_option_manager.option_series_dict.keys()))

    if future_manager is not None:
        print('当前订阅期货合约数量为：{}'.format(len(ctp_manager.current_user.memory.future_manager.index_futures)))
        print('当前订阅期货合约月份为：{}'.format(ctp_manager.current_user.memory.future_manager.index_future_month_id))

    if cffex_option_manager is not None:
        print('当前订阅期权合约数量为：{}'.format(len(ctp_manager.current_user.memory.cffex_option_manager.option_series_dict)))
        print('当前订阅期权合约月份为：{}'.format(ctp_manager.current_user.memory.cffex_option_manager.index_option_month_forward_id))
        print('当前订阅期权合约行权价为：{}'.format(ctp_manager.current_user.memory.cffex_option_manager.option_series_dict['HO2411'].strike_price_options.keys()))




    # print('HO2410的看涨期权的第一个行权价的行权价：{}'.format(ctp_manager.memory.option_manager.index_option_market_data[0, 0, 0, 0]))
    # print('HO2410的看涨期权的第二个行权价的行权价：{}'.format(
    #     ctp_manager.memory.option_manager.index_option_market_data[0, 0, 1, 0]))
    Thread(target=ctp_manager.tick).start()
    if cffex_option_manager is not None:
        Thread(target=ctp_manager.current_user.memory.cffex_option_manager.index_volatility_calculator).start()
    if se_option_manager is not None:
        Thread(target=ctp_manager.current_user.memory.se_option_manager.index_volatility_calculator).start()


    # print('HO2410的看涨期权的第一个行权价相关信息：{}'.format(
    #     ctp_manager.memory.option_manager.index_option_market_data[0, 0, 0]))
    # print('HO2410一共有几个行权价: {}'.format(memory_manager.option_manager.option_month_strike_prices['HO2410']))
    # print('当前订阅期权合约行权价数量为：{}'.format(memory_manager.option_manager.option_month_strike_num))



    # 模拟下单
    # ctp_manager.insert_order('IF2412', Direction.BUY_OPEN, 4000, 2)

    # ctp_manager.query_investor_position_detail()

    while True:
        # k1_volatility = ctp_manager.memory.option_manager.index_option_month_atm_volatility[0, 1]
        # k2_volatility = ctp_manager.memory.option_manager.index_option_month_atm_volatility[0, 2]
        # k3_volatility = ctp_manager.memory.option_manager.index_option_month_atm_volatility[0, 3]
        # k4_volatility = ctp_manager.memory.option_manager.index_option_month_atm_volatility[0, 4]
        # atm_volatility = ctp_manager.memory.option_manager.index_option_month_atm_volatility[0, 5]
        # atm_vega = ctp_manager.memory.option_manager.index_option_month_atm_volatility[0, 6]
        # print(f'HO2410的atm相关信息：k1_volatility: {k1_volatility}, k2_volatility: {k2_volatility}, k3_volatility: {k3_volatility}, k4_volatility: {k4_volatility}, atm_volatility: {atm_volatility}, atm_vega: {atm_vega}')


        # strike_index = 22
        # strike_price = ctp_manager.memory.option_manager.index_option_market_data[1, 0, strike_index, 0]
        # timestamp = ctp_manager.memory.option_manager.index_option_market_data[1, 0, strike_index, 1]
        # bid_price = ctp_manager.memory.option_manager.index_option_market_data[1, 0, strike_index, 2]
        # bid_volume = ctp_manager.memory.option_manager.index_option_market_data[1, 0, strike_index, 3]
        # ask_price = ctp_manager.memory.option_manager.index_option_market_data[1, 0, strike_index, 4]
        # ask_volume = ctp_manager.memory.option_manager.index_option_market_data[1, 0, strike_index, 5]
        # print(f'HO2411的看涨期权的第23个行权价相关信息：行权价{strike_price}, 时间{timestamp}, 买一价{bid_price}, 买一量{bid_volume}, 卖一价{ask_price}, 卖一量{ask_volume}')
        # strike_price = ctp_manager.memory.option_manager.index_option_market_data[1, 1, strike_index, 0]
        # timestamp = ctp_manager.memory.option_manager.index_option_market_data[1, 1, strike_index, 1]
        # bid_price = ctp_manager.memory.option_manager.index_option_market_data[1, 1, strike_index, 2]
        # bid_volume = ctp_manager.memory.option_manager.index_option_market_data[1, 1, strike_index, 3]
        # ask_price = ctp_manager.memory.option_manager.index_option_market_data[1, 1, strike_index, 4]
        # ask_volume = ctp_manager.memory.option_manager.index_option_market_data[1, 1, strike_index, 5]
        # print(f'HO2411的看跌期权的第23个行权价相关信息：行权价{strike_price}, 时间{timestamp}, 买一价{bid_price}, 买一量{bid_volume}, 卖一价{ask_price}, 卖一量{ask_volume}')
        # i = 0
        # call_delta = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 1]
        # put_delta = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 2]
        # gamma = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 3]
        # vega = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 4]
        # call_theta = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 5]
        # put_theta = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 6]
        # vanna_vs = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 7]
        # vanna_sv = ctp_manager.memory.option_manager.index_option_month_greeks[1, i, 8]
        # print(f'HO2411的看涨期权的第一个行权价Greeks相关信息：delta{call_delta}, gamma{gamma}, vega{vega}, theta{call_theta}')
        # print(
        #     f'HO2411的看跌期权的第一个行权价Greeks相关信息：delta{put_delta}, gamma{gamma}, vega{vega}, theta{put_theta}')
        # print('HO2410 期货价格:{}'.format(ctp_manager.memory.option_manager.index_option_month_forward_price[0, :]))
        time.sleep(10)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users')
def get_users():
    result = []
    for user in ctp_manager.users.values():
        resp = UserResp(user.user_id, user.user_name)
        result.append(resp.to_dict())
    return jsonify(result)

@app.route('/api/get_all_market_data', methods=['GET'])
def get_all_market_data():
    # 返回当前行情数据
    return None

@app.route('/api/options', methods=['GET'])
def get_all_option():
    #print(f'get_all_option: {ctp_manager.current_user.memory.option_manager.index_option_month_forward_id}')
    return jsonify(ctp_manager.current_user.memory.cffex_option_manager.index_option_month_forward_id)

@app.route('/api/futures', methods=['GET'])
def get_all_future():
    # print(f'get_all_future: {ctp_manager.current_user.memory.future_manager.index_future_month_id}')
    return jsonify(ctp_manager.current_user.memory.future_manager.index_future_month_id)

# @app.route('/api/option/market_data', methods=['GET'])
# def get_option_forward_price():
#
#     symbol = request.args.get('symbol')
#     option_manager = ctp_manager.current_user.memory.cffex_option_manager
#     resp = OptionMarketResp(symbol)
#
#     try:
#         # 获取 symbol 对应的 index
#         symbol_index = option_manager.index_option_month_forward_id.index(symbol)
#     except ValueError:
#         return jsonify({"error": f"Symbol {symbol} not found"}), 404
#
#     strike_num = option_manager.index_option_month_strike_num[symbol_index]
#
#     for i in range(strike_num):
#         bid = option_manager.index_option_market_data[symbol_index, 0, i, 2]
#         bid_volume = option_manager.index_option_market_data[symbol_index, 0, i, 3]
#         ask = option_manager.index_option_market_data[symbol_index, 0, i, 4]
#         ask_volume = option_manager.index_option_market_data[symbol_index, 0, i, 5]
#         call_option = OptionData(bid, bid_volume, ask, ask_volume)
#
#         bid = option_manager.index_option_market_data[symbol_index, 1, i, 2]
#         bid_volume = option_manager.index_option_market_data[symbol_index, 1, i, 3]
#         ask = option_manager.index_option_market_data[symbol_index, 1, i, 4]
#         ask_volume = option_manager.index_option_market_data[symbol_index, 1, i, 5]
#         put_option = OptionData(bid, bid_volume, ask, ask_volume)
#         resp.strike_prices[option_manager.index_option_market_data[symbol_index, 0, i, 0]] = StrikePrices(call_option, put_option)
#
#     return jsonify(resp.to_dict())

@app.route('/api/option/greeks', methods=['GET'])
def get_option_greeks():
    symbol = request.args.get('symbol')
    if symbol is None or symbol == "":
        return jsonify({"error": f"Symbol invalid"}), 404
    option_manager = ctp_manager.current_user.memory.cffex_option_manager
    resp = OptionGreeksResp(symbol)

    with option_manager.greeks_lock:

        for strike_price, option_tuple in option_manager.option_series_dict[symbol].strike_price_options.items():
            call_delta = option_tuple.call.greeks.delta
            put_delta = option_tuple.put.greeks.delta
            gamma = option_tuple.call.greeks.gamma
            vega = option_tuple.call.greeks.vega
            call_theta = option_tuple.call.greeks.theta
            put_theta = option_tuple.put.greeks.theta
            vanna_vs = option_tuple.call.greeks.vanna_vs
            vanna_sv = option_tuple.call.greeks.vanna_sv
            call_option = OptionGreeksData(call_delta, gamma, vega, call_theta, vanna_vs=vanna_vs, vanna_sv=vanna_sv)
            put_option = OptionGreeksData(put_delta, gamma, vega, put_theta, vanna_vs=vanna_vs, vanna_sv=vanna_sv)
            resp.strike_prices[strike_price] = StrikePrices(call_option, put_option)

    print(resp.to_dict())
    return jsonify(resp.to_dict())

@app.route('/api/option/wing_model', methods=['GET'])
def get_wing_model():
    symbol = request.args.get('symbol')
    if symbol is None or symbol == "":
        return jsonify({"error": f"Symbol invalid"}), 404
    print(f"get wing model parameter for {symbol}")

    try:
        option_series = ctp_manager.current_user.memory.cffex_option_manager.option_series_dict[symbol]
    except ValueError:
        return jsonify({"error": f"Symbol {symbol} not found"}), 404

    option_series = ctp_manager.current_user.memory.cffex_option_manager.option_series_dict[symbol]
    wing_model_para = option_series.wing_model_para
    atm_volatility = option_series.atm_volatility
    resp = WingModelResp(atm_volatility.atm_volatility_protected, wing_model_para.k1, wing_model_para.k2,
                         wing_model_para.b, atm_volatility.atm_valid)
    print(resp.to_dict())
    return jsonify(resp.to_dict())





if __name__ == "__main__":
    init_ctp()
    Thread(target=main).start()
    # app.run(debug=True, use_reloader=False)


