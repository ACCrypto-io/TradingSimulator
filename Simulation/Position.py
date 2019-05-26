import logging
from Utilities import DataHelper, TimeHelper, Consts

logger = logging.getLogger("Position")

# Redis with all coins market data
coins_market_data_getter = DataHelper.DataHelper()


class Position:
    def __init__(self, coin_symbol, order_type, time_ticker, positive_target, negative_target, capital, trailing,
                 fees, leverage_capital, apply_leverage_fees_on_all_capital, leverage, long_trailing_strategy,
                 short_trailing_strategy, time_predict, active_long_investment_strategy,
                 active_short_investment_strategy):
        self.coin_symbol = coin_symbol  # name of the coin
        self.order_type = order_type  # position is short or long
        self.initial_time = time_ticker.current_time  # the timestamp the position has been opened
        self.active = True  # position status
        self.position_end_time = None  # time position finished
        self.position_life_time = time_predict
        self.initial_position_life_time = time_predict
        self.positive_target = positive_target
        self.negative_target = negative_target
        self.current_capital = capital
        self.initial_capital = capital
        self.trailing = trailing  # Boolean
        self.buy_price = []
        self.last_price = None
        self.hit_profit_target = False
        self.hit_loss_target = False
        self.expired = False
        self.stopped = False
        self.liquidated = False
        self.trailing_activated = 0
        self.long_trailing_strategy = long_trailing_strategy
        self.short_trailing_strategy = short_trailing_strategy
        self.active_long_investment_strategy = active_long_investment_strategy
        self.active_short_investment_strategy = active_short_investment_strategy
        self.fees = fees
        self.hours_position_open = 0
        self.fees_paid = 0
        self.leverage_capital = leverage_capital
        self.leverage = leverage
        self.time_ticker = time_ticker
        self.apply_leverage_fees_on_all_capital = apply_leverage_fees_on_all_capital

        # Initializes position once created
        self.enter_position()

        logger.debug(
            "{} position for {} in {} has been created successfully with {} capital which includes {} leverage, with the cost of {} fees".format(
                self.order_type,
                self.coin_symbol, TimeHelper.epoch_to_date_time(self.initial_time), self.initial_capital,
                self.leverage_capital, self.fees_paid))

    def enter_position(self):
        """
        Enters position and updates capital accordingly
        :return:
        """

        success, data = coins_market_data_getter.get_coin_data(int(self.initial_time), self.coin_symbol)
        if not success:
            logger.error("No open price for coin {} at time {}".format(self.coin_symbol, self.initial_time))
            raise Exception

        # Update buy price
        self.buy_price.append(data['_open'])
        self.last_price = data['_open']

        leverage_fee = 0

        # Calculate fees
        if self.leverage > 1:
            leverage_fee = self.fees.apply_leverage_buy_fees(self.coin_symbol, self.leverage_capital)

        capital_taker_fee = self.fees.apply_taker_fee(self.coin_symbol, self.current_capital)

        # Update paid fees
        self.fees_paid = capital_taker_fee + leverage_fee

        # Update current capital minus takers fee
        self.current_capital = self.current_capital - capital_taker_fee - leverage_fee

    def updates_new_time_is_liquidate(self, ml_results=None):
        """
        Updates capital and hours positions open according to new time
        :return: Boolean if liquidated or not
        """

        # Updates Capital
        success, coins_data = \
            coins_market_data_getter.get_coin_data(int(self.time_ticker.current_time), self.coin_symbol)

        if not success:
            logger.error("No open price for coin {} at time {}".format(self.coin_symbol, self.initial_time))
            raise Exception("No open price for coin {} at time {}".format(self.coin_symbol, self.initial_time))

        new_price = coins_data['_open']

        # If Long then we profit from positive change and if short we profit from negative change
        if self.order_type == Consts.LONG:
            current_change = (new_price / self.last_price) - 1
        else:
            current_change = ((new_price / self.last_price) - 1) * (-1)

        self.current_capital += (self.current_capital * current_change)

        # Updates last price
        self.last_price = new_price

        # Updates hours position opened
        self.hours_position_open += self.time_ticker.hours_tick_time_interval

        # Check if position got liquidated
        if self.current_capital <= self.leverage_capital:
            logger.error("The position with coin symbol: {} got liquidated at {}".format(self.coin_symbol,
                                                                                         TimeHelper.epoch_to_date_time(
                                                                                             self.time_ticker.current_time)))
            self.liquidated = True
            self.close_position()
            return True
        else:
            return False

    def apply_time_leverage_fees(self):
        """
        Checks if its time fo leverage fees and updates position stats accordingly
        :return:
        """
        if self.fees.is_it_time_for_leverage_fee(self.coin_symbol,
                                                                               self.hours_position_open):
            if self.apply_leverage_fees_on_all_capital:
                fees_current_capital = self.fees.apply_leverage_time_for_fee_in_hours(self.coin_symbol,
                                                                                      self.current_capital)

                # Update paid fees
                self.fees_paid += fees_current_capital

                # Update current capital minus fees
                self.current_capital -= fees_current_capital

            else:
                fees_leverage_capital = self.fees.apply_leverage_time_for_fee_in_hours(self.coin_symbol,
                                                                                       self.leverage_capital)
                # Update paid fees
                self.fees_paid += fees_leverage_capital

                # Update current capital minus fees
                self.current_capital -= fees_leverage_capital

    def reach_target_update(self, ml_results=None):
        """
        Checks if position reached target, and updates accordingly
        :return: Boolean if reach positive or negative target
        """
        success, coins_data = coins_market_data_getter.get_coin_data(int(self.time_ticker.current_time), self.coin_symbol)

        if not success:
            raise Exception

        diff_high = ((coins_data['_high'] / self.buy_price[-1]) - 1)
        diff_low = ((coins_data['_low'] / self.buy_price[-1]) - 1)

        if coins_data['_high'] / coins_data['_low'] > 2:
            logger.error("In time {} there was 2 times jump between high and low price for coin {}".format(TimeHelper.epoch_to_date_time(self.time_ticker.current_time), self.coin_symbol))
            self.hit_loss_target += 1
            self.close_position(profit=False)
            return True

        if diff_high >= self.positive_target and diff_low <= self.negative_target:
            logger.error("In time {} the price reached the high and low boundary for coin {}".format(TimeHelper.epoch_to_date_time(self.time_ticker.current_time), self.coin_symbol))
            self.hit_loss_target += 1
            self.close_position(profit=False)
            return True

        # If hits target for short or long
        if (diff_low <= self.negative_target and self.order_type == Consts.SHORT) or (
                        diff_high >= self.positive_target and self.order_type == Consts.LONG):

            # If trailing is on, apply
            if self.trailing:
                if (self.order_type == Consts.SHORT and len(self.short_trailing_strategy) != 0) or (self.order_type == Consts.LONG and len(self.long_trailing_strategy) != 0):
                    self.handle_trailing()
                    return False

            self.close_position(profit=True)
            self.hit_profit_target = True
            return True

        # if miss target for short or long
        elif (diff_high >= self.positive_target and self.order_type == Consts.SHORT) or (
                        diff_low <= self.negative_target and self.order_type == Consts.LONG):
            self.close_position(profit=False)
            self.hit_loss_target = True
            return True

        # Did not reach either targets
        else:
            return False

    def handle_trailing(self):
        """
        Updates position according to trailing strategy and resets the buy price
        :return:
        """

        # Reset buy price to current price
        self.buy_price.append(self.last_price)

        # Update that trailing has been applied
        self.trailing_activated += 1

        # Extend position life time
        self.position_life_time = (self.position_life_time * 2)

        if self.order_type == Consts.SHORT:
            self.positive_target = self.short_trailing_strategy['high_boundary']
            self.negative_target = self.short_trailing_strategy['low_boundary']
        else:
            self.positive_target = self.long_trailing_strategy['high_boundary']
            self.negative_target = self.long_trailing_strategy['low_boundary']

    def close_position(self, profit=None):
        """
        Close position
        :return:
        """

        # close position
        self.active = False
        self.position_end_time = self.time_ticker.current_time

        # # If the position was closed by reaching a limit then calculating the diff from the relevant target
        # if profit is not None:
        #
        #     # current_change = 0
        #     # change_from_buy_price = (self.last_price / self.buy_price[-1]) - 1
        #     diff_high = (self.positive_target / self.last_price) - 1
        #     # diff_low = (self.negative_target / change_from_buy_price) - 1
        #
        #     if profit:
        #         if self.order_type == Consts.LONG:
        #             current_change = diff_high
        #         elif self.order_type == Consts.SHORT:
        #             current_change = -diff_low
        #     else:
        #         if self.order_type == Consts.LONG:
        #             current_change = diff_low
        #         elif self.order_type == Consts.SHORT:
        #             current_change = -diff_high
        #     self.current_capital += (self.current_capital * current_change)

        leverage_sell_fee = 0

        # Fetch leverage fee if exist
        if self.leverage > 1:
            leverage_sell_fee = self.fees.apply_leverage_sell_fees(self.coin_symbol, self.leverage_capital)

        # Calculate the taker fee
        taker_capital_sell_fee = self.fees.apply_taker_fee(self.coin_symbol, self.current_capital)

        # Update paid fees
        self.fees_paid = self.fees_paid + leverage_sell_fee + taker_capital_sell_fee

        # Update current capital minus fees
        self.current_capital = self.current_capital - taker_capital_sell_fee - leverage_sell_fee

    def is_expired(self, ml_results=None):
        """
        Checks if position is expired
        :return: Boolean
        """

        if self.hours_position_open == self.position_life_time:
            self.expired = True
            self.close_position()
            return True
        else:
            return False

    def force_close(self, ml_results=None):
        self.expired = True
        self.close_position()

    def is_active_invest_strategy(self, ml_results=None):
        """
        Checks if position needs to be closed according to ml results
        :param ml_results:
        :return: Boolean
        """

        if self.coin_symbol in ml_results.coin_symbol.tolist():

            prob_negative = ml_results.loc[ml_results['coin_symbol'] == self.coin_symbol, Consts.PROB_NEGATIVE_HEADER].values[0]
            prob_positive = ml_results.loc[ml_results['coin_symbol'] == self.coin_symbol, Consts.PROB_POSITIVE_HEADER].values[0]
            # TODO: add the other probabilities
            if self.order_type == Consts.LONG and len(self.active_long_investment_strategy) != 0:
                if self.active_long_investment_strategy['max_prob_negative'] <= prob_negative:
                    self.stopped = True
                    self.close_position()
                    return True
            elif self.order_type == Consts.SHORT and len(self.active_short_investment_strategy) != 0:
                if self.active_short_investment_strategy['max_prob_positive'] <= prob_positive:
                    self.stopped = True
                    self.close_position()
                    return True

        return False

    def get_current_liquid_capital(self):
        """
        Returns current liquid capital.
        :return: Float
        """
        return self.current_capital - self.leverage_capital

    def get_roi_status(self):
        """
        Returns current ROI for position
        :return: Float
        """
        return (self.current_capital - self.leverage_capital) / (self.initial_capital - self.leverage_capital)
