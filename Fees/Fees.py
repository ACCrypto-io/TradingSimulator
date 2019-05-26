from Utilities import Consts
import pandas as pd

# Default fees
DEFAULT_MAKER_FEE = 0.0075
DEFAULT_TAKER_FEE = 0.009
DEFAULT_LEVERAGE_SELL_FEES = 0.00075
DEFAULT_LEVERAGE_BUY_FEES = 0.00075
DEFAULT_LEVERAGE_TIME_FOR_FEES_IN_HOURS = 24
DEFAULT_LEVERAGE_FEE_FOR_INTERVAL_TIME = 0.0015


class Fees:
    def __init__(self):
        self.fees_individual_df = pd.read_csv(Consts.FEES_FILE_PATH + Consts.FEES_FILE_NAME)
        self.fees_individual_df.set_index(['coin_symbol'], inplace=True)

    def apply_maker_fee(self, coin_symbol, capital):
        """

        :param coin_symbol:
        :param capital:
        :return:
        """
        # TODO: implement

    def apply_taker_fee(self, coin_symbol, capital):
        """
        applies taker fee for coin by capital
        :param coin_symbol:
        :param capital:
        :return: float : fee
        """
        if coin_symbol in self.fees_individual_df.index.values.tolist():
            return capital * self.fees_individual_df.loc[coin_symbol, 'taker_fee']
        else:
            return capital * DEFAULT_TAKER_FEE

    def apply_leverage_sell_fees(self, coin_symbol, capital):
        """
        applies leverage sell fees
        :param coin_symbol:
        :param capital:
        :return: float : fee
        """
        if coin_symbol in self.fees_individual_df.index.values.tolist():
            return capital * self.fees_individual_df.loc[coin_symbol, 'leverage_sell_fee']
        else:
            return capital * DEFAULT_LEVERAGE_SELL_FEES

    def apply_leverage_buy_fees(self, coin_symbol, capital):
        """
        applies leverage buy fee.
        :param coin_symbol:
        :param capital:
        :return: float: fee
        """
        if coin_symbol in self.fees_individual_df.index.values.tolist():
            return capital * self.fees_individual_df.loc[coin_symbol, 'leverage_buy_fee']
        else:
            return capital * DEFAULT_LEVERAGE_BUY_FEES

    def apply_leverage_time_for_fee_in_hours(self, coin_symbol, capital):
        """
        Return the amount of fees needed to be paid
        :param coin_symbol:
        :param capital:
        :return: Float - fees
        """
        if coin_symbol in self.fees_individual_df.index.values.tolist():
            return capital * self.fees_individual_df.loc[coin_symbol, 'leverage_fees_for_time_interval']

        else:
            return capital * DEFAULT_LEVERAGE_FEE_FOR_INTERVAL_TIME

    def is_it_time_for_leverage_fee(self, coin_symbol, hours_position_open):
        """
        Checks if its time to pay leverage fee
        :return: Boolean if its time for leverage or not
        """
        if coin_symbol in self.fees_individual_df.index.values.tolist():
            if hours_position_open % self.fees_individual_df.loc[coin_symbol, 'leverage_time_for_fees_in_hours'] == 0 \
                    and hours_position_open > 0:
                return True
        elif hours_position_open == DEFAULT_LEVERAGE_TIME_FOR_FEES_IN_HOURS:
            return True
        return False
