import time

import numpy as np
from ctp_manager import CTPManager
from memory.memory_manager import MemoryManager


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

    instrument_ids = ctp_manager.trader_user_spi.exchange_id.keys()
    print('当前订阅的合约数量为:{}'.format(len(instrument_ids)))

    # 初始化内存
    memory_manager = MemoryManager(instrument_ids)
    print('当前订阅期货合约数量为：{}'.format(len(memory_manager.futures)))
    print('当前订阅期权合约数量为：{}'.format(len(memory_manager.options)))

    # 订阅合约
    ctp_manager.subscribe_market_data_in_batches(instrument_ids)


    # ctp_manager.insert_order('IF2412', "buyopen", 4160, 2)

    # ctp_manager.query_investor_position_detail()

    while True:
        print("Heartbreak...")
        time.sleep(10)

if __name__ == "__main__":
    main()