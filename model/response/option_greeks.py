from model.response.option_resp_base import OptionRespBase


class OptionGreeksResp(OptionRespBase):
    pass


class OptionGreeksData:
    def __init__(self, delta, gamma, vega, theta, vanna_vs, vanna_sv, position):
        self.delta = round(delta, 2)
        self.gamma = round(gamma, 2)
        self.vega = round(vega, 2)
        self.theta = round(theta, 2)
        self.vanna_vs = round(vanna_vs, 2)
        self.vanna_sv = round(vanna_sv, 2)
        self.position = position

    def to_dict(self):
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "vega": self.vega,
            "theta": self.theta,
            "vanna_vs": self.vanna_vs,
            "vanna_sv": self.vanna_vs,
            "position": self.position
        }

