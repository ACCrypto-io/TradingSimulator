import logging
from Simulation import Position
from Utilities import Consts, TimeHelper
from scipy.stats import norm
from Utilities import DataHelper
from Simulation.Statistics import Stats

logger = logging.getLogger("Portfolio")

# Redis with all coins market data
coins_market_data_getter = DataHelper.DataHelper()


class Portfolio(Stats):
    def __init__(self, df_simulation, fees, TimeTicker):

        # Inherit from stats, and initialize with capital
        Stats.__init__(self, df_simulation['amount_of_capital'].iloc[0])

        self.trailing_strategy = df_simulation['trailing_strategy'].iloc[
            0]  # Object which represents the trailing strategy
        self.shorts = df_simulation['shorts'].iloc[0]  # Boolean
        self.longs = df_simulation['longs'].iloc[0]  # Boolean
        self.leverage = df_simulation['leverage'].iloc[
            0]  # int between 1 - .... - represents the multiplier of the leverage
        self.min_prob_for_leverage = df_simulation['min_prob_for_leverage'].iloc[
            0]  # the min probability for a prediction in order to apply leverage
        self.max_percent_cap_investment_in_a_round = df_simulation[
            'max_percent_cap_investment_in_a_round'].iloc[
            0]  # in every new investment round(may include several positions), how much percentage out of total capital is available.
        self.max_percent_out_of_volume = df_simulation[
            'max_percent_out_of_volume'].iloc[
            0]  # in every new position, what is the maximum percentage to invest out of the coin volume
        self.long_investment_strategy = df_simulation['long_investment_strategy'].iloc[
            0]  # loads long investment strategies
        self.short_investment_strategy = df_simulation['short_investment_strategy'].iloc[
            0]  # loads short investment strategies
        self.active_short_investment_strategy = df_simulation[
            'active_short_investment_strategy'].iloc[0]  # loads active investment strategies
        self.active_long_investment_strategy = df_simulation[
            'active_long_investment_strategy'].iloc[0]  # loads active investment strategies
        self.min_investment = df_simulation['min_investment'].iloc[0]  # min amount in usd to invest in a single coin
        self.accept_short_and_long_same_tick_and_symbol = \
            df_simulation['accept_short_and_long_same_tick_and_symbol'].iloc[
                0]  # Boolean - if to accept a short an long prediction on a specific coin at the same time.
        self.apply_leverage_fees_on_all_capital = df_simulation['apply_leverage_fees_on_all_capital'].iloc[0]  #
        self.long_trailing_strategy = df_simulation['long_trailing_strategy'].iloc[0]
        self.short_trailing_strategy = df_simulation['short_trailing_strategy'].iloc[0]
        self.time_ticker = TimeTicker  # Tracks the current time of the portfolio
        self.fees = fees  # List of specific fees for specific coin_symbols

        logger.info("The Portfolio has been created successfully with capital: {}".format(self.liquid_capital))

    def is_there_open_positions(self):
        """
        Checks if there are open positions in portfolio
        :return: Boolean
        """
        if len(self.active_long_positions + self.active_short_positions) > 0:
            return True
        else:
            return False

    def closed_positions(self, closed_pos):
        """
        Actions which reflects a closed position
        :param closed_pos: A list of closed positions
        :return: None
        """
        liquidated_short_capital = 0
        liquidated_long_capital = 0
        leveraged_capital = 0
        fees_paid = 0

        for pos in closed_pos:
            if pos.order_type == Consts.SHORT:
                liquidated_short_capital += pos.get_current_liquid_capital()
            else:
                liquidated_long_capital += pos.get_current_liquid_capital()

            # Calculates the amount of fees for the current closed position.
            fees_paid += pos.fees_paid

            # Calculates the amount of leveraged capital for current closed position.
            leveraged_capital += pos.leverage_capital

            # Update if trailing has been activate
            if pos.trailing_activated > 0:
                self.hit_trail_positions += pos.trailing_activated

            # Update hit/miss/expired/stopped counters
            if pos.hit_profit_target:
                self.hit_positions += 1
            elif pos.expired:
                self.expired_positions_counter += 1
            elif pos.stopped:
                self.stopped_positions_counter += 1
            else:
                self.miss_positions += 1

        # Update portfolio statistics according to the closed position
        self.fees_paid += fees_paid
        self.liquid_capital += liquidated_long_capital + liquidated_short_capital
        self.leverage_capital -= leveraged_capital

    def updater(self, func_name, ml_results=None):
        """
        The updater applies different functions which requires to close a position upon all active positions.
        The functions returns boolean that indicates if the position which the function was applied on need to be closed.
        :param func_name: The string of the function name in Position Class.
        :param ml_results: If required the ml result of the current time for the function
        :return:
        """

        closed_pos = []

        # Iterates all active positions
        for pos in self.active_short_positions + self.active_long_positions:

            # Check if position reached target /expired / active strategy, and updates the position accordingly
            if getattr(pos, func_name)(ml_results=ml_results):

                closed_pos.append(pos)

                if pos.order_type == Consts.LONG and self.longs:
                    self.active_long_positions.remove(pos)
                    self.closed_long_positions.append(pos)
                if pos.order_type == Consts.SHORT and self.shorts:
                    self.active_short_positions.remove(pos)
                    self.closed_short_positions.append(pos)

        # Updates Portfolio stats according to new closed positions
        self.closed_positions(closed_pos)

        # Updates capital stats after last operations
        self.update_capital_stats()

    def apply_time_leverage_fees(self):
        """
        applies leverage fee on active positions with leverage
        :return:
        """
        if len(self.active_long_positions + self.active_short_positions) == 0:
            return

        if self.leverage > 1:
            for pos in (self.active_long_positions + self.active_short_positions):
                pos.apply_time_leverage_fees()

            self.update_capital_stats()

    def update_capital_stats(self):
        """
        Updates capital statistics according to all open positions
        :return:
        """
        short_capital = 0
        long_capital = 0

        for pos in (self.active_long_positions + self.active_short_positions):

            if pos.order_type == Consts.LONG:
                long_capital += pos.get_current_liquid_capital()
            else:
                short_capital += pos.get_current_liquid_capital()

        self.short_capital = short_capital
        self.long_capital = long_capital

    def enter_new_positions(self, current_ml_results):
        """"
        Iterates MLResults and handles each one
        :param current_ml_results: df
        :return: None
        """

        # If we simulation does not accept short and long positon on the same coin at the same time
        if not self.accept_short_and_long_same_tick_and_symbol:
            current_ml_results = current_ml_results.drop_duplicates('coin_symbol')

        if not self.longs:
            current_ml_results = current_ml_results[current_ml_results['order_type'] != Consts.LONG]

        if not self.shorts:
            current_ml_results = current_ml_results[current_ml_results['order_type'] != Consts.SHORT]

        index_to_delete = []
        # Iterate ml results and add to new_positions accordingly
        for index, row in current_ml_results.copy().iterrows():

            # Skip prediction if simulation is limited to invest in specific coins. Notice, if the list is ALL then the simulation has no limitations.
            coin_symbol = row['coin_symbol']

            success, coin_current_volume = self.fetch_coins_24h_volumeto(coin_symbol)

            # exit if failed to fetch volume
            if not success:
                raise Exception

            # Volume boundary of the specific coin symbol at the specific time
            coins_max_capital_volume_boundary = self.max_percent_out_of_volume * coin_current_volume

            # Not enough volume to invest
            if coins_max_capital_volume_boundary < self.min_investment:
                logger.warning("Not enough volume to invest in {} at {}".format(coin_symbol,
                                                                                TimeHelper.epoch_to_date_time(
                                                                                    self.time_ticker.current_time)))
                index_to_delete.append(index)
                continue

            prob_positive = row[Consts.PROB_POSITIVE_HEADER]
            prob_negative = row[Consts.PROB_NEGATIVE_HEADER]

            # Check if we should invest long according to long investment strategy then remain in df. If not, deletes the prediction from current_ml_results
            if row['order_type'] == Consts.LONG and not self.is_long_according_to_invest_strategy(
                    prob_positive,
                    prob_negative):
                index_to_delete.append(index)

            # Check if we should invest short according to short investment strategy then remain. If not, deletes the prediction from current_ml_results
            elif row['order_type'] == Consts.SHORT and not self.is_short_according_to_invest_strategy(
                    prob_positive, prob_negative):
                index_to_delete.append(index)
        current_ml_results.drop(index_to_delete, inplace=True)
        # There are no new positions
        if len(current_ml_results) == 0:
            logger.debug("There are no new positions according to current strategy, at time: {}".format(
                TimeHelper.epoch_to_date_time(self.time_ticker.current_time)))
        else:
            self.invest(current_ml_results)

    def invest(self, new_positions):
        """
        Invests in new positions.
        :param new_positions: df
        :return:
        """

        # Add three columns to df and initialize
        new_positions.loc[:, Consts.FULLY_INVESTED] = False
        new_positions.loc[:, Consts.CAPITAL_TO_INVEST] = 0
        new_positions.loc[:, Consts.LEVERAGED_CAPITAL] = 0

        # Available capital for current round
        available_capital = self.liquid_capital * self.max_percent_cap_investment_in_a_round

        if available_capital < self.min_investment:
            logger.debug(
                "The available capital for this round is smaller then the min investment. There are no new positions for time:{}".format(
                    TimeHelper.epoch_to_date_time(self.time_ticker.current_time)))
            return

        # Adds 'capital_to_invest' column and 'fully_invested' column to each row
        new_positions = self.capital_allocation_strategy(new_positions,
                                                         available_capital)

        if len(new_positions) == 0:
            logger.debug(
                "There are no new positions for time:{}".format(
                    TimeHelper.epoch_to_date_time(self.time_ticker.current_time)))
            return

        # If simulation has leverage, fills Consts.LEVERAGE_CAPITAL with relevant leverage
        if self.leverage > 1:
            new_positions = self.add_leverage_by_conditions(new_positions)

        # Create new positions
        for index, position in new_positions.iterrows():
            order_type = position['order_type']

            # Create a new position
            pos = Position.Position(position['coin_symbol'], order_type, self.time_ticker,
                                    position['high_boundary'], position['low_boundary'],
                                    position['capital_to_invest'] + position[Consts.LEVERAGED_CAPITAL],
                                    self.trailing_strategy, self.fees, position[Consts.LEVERAGED_CAPITAL],
                                    self.apply_leverage_fees_on_all_capital, self.leverage, self.long_trailing_strategy,
                                    self.short_trailing_strategy, position['time_predict'],
                                    self.active_long_investment_strategy, self.active_short_investment_strategy)

            # Allocates each order to its relevant statistics
            if order_type == Consts.SHORT:
                self.active_short_positions.append(pos)
                self.short_capital += pos.get_current_liquid_capital()
            else:
                self.active_long_positions.append(pos)
                self.long_capital += pos.get_current_liquid_capital()

            # Update portfolio liquid capital and leverage capital
            self.liquid_capital -= pos.get_current_liquid_capital()
            self.leverage_capital += pos.leverage_capital

        logger.debug("Finished investment cycle for time {}".format(
            TimeHelper.epoch_to_date_time(self.time_ticker.current_time)))
        logger.debug(
            "liquid capital: {}, leverage capital: {}, long capital: {}, short capital: {}".format(self.liquid_capital,
                                                                                                   self.leverage_capital,
                                                                                                   self.long_capital,
                                                                                                   self.short_capital))

    def add_leverage_by_conditions(self, new_positions):
        """
        if leverage condition is bigger then the prob_positive (in long case) or the prob_negative (in short case) then adds to leverage column the amount.
        :param new_positions: df
        :return: new_positions df with leverage column accordingly
        """

        for index, coin_data_to_invest in new_positions.copy().iterrows():

            # If long position we check that the prob positive stands in the min prob for leverage condition
            if coin_data_to_invest['order_type'] == Consts.LONG:
                if coin_data_to_invest[Consts.PROB_POSITIVE_HEADER] >= self.min_prob_for_leverage:
                    new_positions.loc[index, Consts.LEVERAGED_CAPITAL] = (coin_data_to_invest[
                                                                              'capital_to_invest'] * self.leverage) - \
                                                                         coin_data_to_invest['capital_to_invest']

            # If short position we check that the prob negative stands in the min prob for leverage condition
            else:
                if coin_data_to_invest[Consts.PROB_NEGATIVE_HEADER] >= self.min_prob_for_leverage:
                    new_positions.loc[index, Consts.LEVERAGED_CAPITAL] = (coin_data_to_invest[
                                                                              'capital_to_invest'] * self.leverage) - \
                                                                         coin_data_to_invest['capital_to_invest']
        return new_positions

    @staticmethod
    def calc_invest(prob):
        """
        Calculation according to literature
        :param prob:
        :return:
        """
        if prob == 1.0:
            prob = 0.999
        elif prob == 0.0:
            prob = 0.001

        signal = (prob - (1.0 / Consts.NUM_OF_CLASSES)) / ((prob * (1.0 - prob)) ** 0.5)

        res = (2 * norm.cdf(signal) - 1)

        return res

    def percent_capital_according_to_probability(self, prob_pos, prob_neg, order_type):
        """
        Calculates the percentage of capital to invest.
        :param prob_pos: The probability of the positive output
        :param prob_neg: The probability of the negative output
        :param order_type: short/long
        :return: The percentage of capital to invest out of max_amount_to_invest_in_coin
        """
        pos = self.calc_invest(prob_pos)
        neg = self.calc_invest(prob_neg)

        # TODO: CAN BE DONE BETTER
        if order_type == Consts.LONG:
            return pos
            # if neg < neutral:
            #     return pos
            # else:
            #     return pos - abs(neg)
        else:
            return neg
            # if pos < neutral:
            #     return neg
            # else:
            #     return neg - abs(pos)

    def capital_allocation_strategy(self, coins_to_invest, available_capital):
        """
        Recursive function which allocates funds according to simulation conditions and then allocates capital according to probability and 24h volume
        :param coins_to_invest:
        :param available_capital:
        :return: coins_to_invest and Adds 'capital_to_invest' column and 'fully_invested' column to each row
        """
        coins_available_capital = 0
        used_capital = 0

        # Count positions which capital size is not equal to max capacity of investment
        total_positions_count = len(coins_to_invest[coins_to_invest[Consts.FULLY_INVESTED] == False])

        if total_positions_count > 0:

            # Divide all available capital equally by all the positions
            coins_available_capital = available_capital / total_positions_count

        # Stopping condition: If there are no more position not fully invested or coins_available_capital is smaller then min investment
        if total_positions_count == 0 or coins_available_capital < self.min_investment:
            return coins_to_invest

        # Iterate all coins to invest which are not fully invested
        for index, coins_prediction in coins_to_invest[coins_to_invest[Consts.FULLY_INVESTED] == False].copy().iterrows():

            coin_symbol = coins_prediction['coin_symbol']

            success, coin_current_volume = self.fetch_coins_24h_volumeto(coin_symbol)

            # exit if failed to fetch volume
            if not success:
                raise Exception

            if coin_current_volume == 0.0:
                logger.debug("Volume is zero. Not investing in: {}, at time: {}".format(coin_symbol,
                                                                                        TimeHelper.epoch_to_date_time(
                                                                                            self.time_ticker.current_time)))
                coins_to_invest.loc[index, Consts.FULLY_INVESTED] = True
                continue

            # Volume boundary of the specific coin symbol at the specific time
            coins_max_capital_volume_boundary = self.max_percent_out_of_volume * coin_current_volume

            # If the volume boundary is smaller then available capital, then there is maximum capital in current position means = fully invested
            if coins_max_capital_volume_boundary < coins_available_capital:
                coins_to_invest.loc[index, Consts.FULLY_INVESTED] = True
                max_amount_to_invest_in_coin = coins_max_capital_volume_boundary
            else:
                max_amount_to_invest_in_coin = coins_available_capital

            # Risk indicator which decreases positions size according to probability
            capital_percent = self.percent_capital_according_to_probability(coins_prediction[Consts.PROB_POSITIVE_HEADER],
                                                                            coins_prediction[Consts.PROB_NEGATIVE_HEADER],
                                                                            coins_prediction['order_type'])

            current_capital_to_invest_in_position = capital_percent * max_amount_to_invest_in_coin

            # Add to capital to invest for current row
            coins_to_invest.loc[index, Consts.CAPITAL_TO_INVEST] = coins_to_invest.loc[
                                                                       index, Consts.CAPITAL_TO_INVEST] + current_capital_to_invest_in_position

            used_capital += current_capital_to_invest_in_position

        available_capital -= used_capital

        return self.capital_allocation_strategy(coins_to_invest, available_capital)

    def fetch_coins_24h_volumeto(self, coin_symbol):
        """
        Aggregated volumeto for the last 24h
        :param coin_symbol:
        :return: success, volumeto24h
        """
        volumeto = 0
        hours_to_calculate = 25
        counter = 1
        while counter <= hours_to_calculate:
            _time_to_fetch = self.time_ticker.current_time - (counter * 60 * 60)
            success, coins_market = coins_market_data_getter.get_coin_data(int(_time_to_fetch),
                                                                           coin_symbol)
            if not success:
                logger.error("Skipping coin {}, there is no market data from db in {}".format(coin_symbol,
                                                                                              TimeHelper.epoch_to_date_time(
                                                                                                  _time_to_fetch)))
                raise Exception

            volumeto += coins_market['_volumeto']
            counter += 1
        return True, volumeto

    def is_long_according_to_invest_strategy(self, prob_positive, prob_negative):
        """
        Checks if the conditions meets the investment strategy
        :return: Boolean
        """

        return prob_positive >= self.long_investment_strategy['min_prob_positive'] and \
               prob_negative < self.long_investment_strategy['max_prob_negative']

    def is_short_according_to_invest_strategy(self, prob_positive, prob_negative):
        """
        Checks if the conditions meets the investment strategy
        :return: Boolean
        """
        return prob_positive < self.short_investment_strategy['max_prob_positive'] and \
               prob_negative >= self.short_investment_strategy['min_prob_negative']
