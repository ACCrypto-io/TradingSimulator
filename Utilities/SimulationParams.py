import logging
import sys
from Utilities import Consts


class SimulationParamsOptions:
    def __init__(self):
        self.TRAILING_STRATEGY = [True]  # Set always to True.
        self.MAX_PERCENT_CAP_INVESTMENT_IN_A_ROUND = [0.2, 0.1]  # Every x time alto produces a prediction.
        # This percentage applies to max amount of capital allocated for a prediction output.
        self.AMOUNT_OF_CAPITAL = [1000000.0]  # Amount of initial capital for a simulation.
        self.MAX_PERCENT_OUT_OF_VOLUME = [0.01]  # Max percentage out of a coin volume which can be invested.
        self.COINS_TO_INVEST_IN = [[Consts.ALL]]  # Set the coins that should be invested, for all set [[Consts.ALL]].
        self.SHORTS = [True]  # Should invest shorts.
        self.LONGS = [True]  # Should invest longs.
        self.LEVERAGE = [1]  # Leverage amount.
        self.MIN_INVESTMENT = [10000.0]  # The minimum investment per position.
        self.MIN_PROB_FOR_LEVERAGE = [0.8]  # If leverage is enable then create a position with leverge when.
        # probability is at least the number you set
        self.ACCEPT_SHORT_AND_LONG_SAME_TICK_AND_SYMBOL = [True]  # Set always to True.
        self.APPLY_LEVERAGE_FEES_ON_ALL_CAPITAL = [False]  # If True, once its time for leverage fees it will be taken
        # from all capital. If false it will be taken only from leverage capital.

        # Set the probability to create a long position (e.x. if set {'min_prob_positive': 0.7, 'max_prob_negative': 0.4}
        # then the simulation will invest only when a prediction have at least 0.7 in the positive probability and no
        # more then 0.4 in the negative probability.
        self.LONG_INVESTMENT_STRATEGY = [
            {
                'min_prob_positive': 0.8,
                'max_prob_negative': 0.2,
            },
        ]

        # Same explanation as long but here we activate the shorts.
        self.SHORT_INVESTMENT_STRATEGY = [
            {
                'min_prob_negative': 0.8,
                'max_prob_positive': 0.4,
            },
        ]

        # Trailing is when a position reached its profit limit then instead of closing the position it will set a new
        # high boundary and low boundary as set here from the profit limit price.
        self.LONG_TRAILING_STRATEGY = [
            {},  # No trailing
            # {
            #     'high_boundary': 0.03,
            #     'low_boundary': -0.01
            # },
            {
                'high_boundary': 0.06,
                'low_boundary': -0.02
            },
        ]

        # Same as the long trailing strategy.
        self.SHORT_TRAILING_STRATEGY = [
            {},  # No trailing
            # {
            #     'high_boundary': 0.01,
            #     'low_boundary': -0.03
            # },
            {
                'high_boundary': 0.02,
                'low_boundary': -0.06
            },
        ]

        # If there is a position and a prediction show that the position will loose, you can set here when to sell a
        # position.
        self.ACTIVE_LONG_INVESTMENT_STRATEGY = [
            {
                'max_prob_negative': 0.5,
                'min_prob_positive': 0.6,
            },
            {}
        ]

        # Same as active long investment strategy.
        self.ACTIVE_SHORT_INVESTMENT_STRATEGY = [
            {},
            {
                'max_prob_positive': 0.3,
                'min_prob_negative': 0.5,
            },
        ]


LOGGING_FORMAT = "%(levelname)-8s %(module)-22s:%(lineno)-4s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT, stream=sys.stdout)
