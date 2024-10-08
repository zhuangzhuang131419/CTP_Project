from model.instrument.option import Option


class OptionSeries:
    CALL = 0  # 看涨期权在列表中的位置
    PUT = 1  # 看跌期权在列表中的位置

    def __init__(self, name: str, options: [Option]):
        """
        初始化期权系列。

        :param name: 期权的名字，例如 'HO2410' 表示某个品种（HO）和月份（2410）的期权系列。
        :param options: 期权对象列表，包含该系列的所有期权。
        """
        self.name = name # 期权名字，例如 'HO2410'
        self.strike_price_options = {}

        for option in options:
            if option.strike_price not in self.strike_price_options:
                self.strike_price_options[option.strike_price] = [None, None]

            if option.is_call_option():
                self.strike_price_options[option.strike_price][self.CALL] = option
            elif option.is_put_option():
                self.strike_price_options[option.strike_price][self.PUT] = option

        self.strike_price_options = dict(sorted(self.strike_price_options.items()))

    def get_option(self, strike_price, is_put):
        return self.strike_price_options[strike_price][is_put]

    def get_all_options(self):
        """
        获取所有非空的期权（看涨期权和看跌期权）。
        :return: 所有期权的列表。
        """
        return [option for pair in self.strike_price_options.values() for option in pair if option is not None]

    def get_all_strike_price(self):
        return list(self.strike_price_options.keys())

    def get_num_strike_price(self):
        return len(self.strike_price_options.keys())

