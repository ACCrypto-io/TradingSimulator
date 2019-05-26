import logging
import pandas as pd
from Analytics import AnalyticsFactory
from Simulation import Portfolio, TimeTicker
from Utilities import Consts, TimeHelper
from Utilities.DataHelper import DataHelper

logger = logging.getLogger("Simulation")

data_helper = DataHelper()


class Simulation:
    def __init__(self,
                 params):  # params_order = (ml_results_df, df_simulation, tick_time_hours, fees, _current_time, coins_for_benchmark)
        self.ml_results_df = params[0]  # All ml result for current simulation
        self.df_simulation = params[1]  # Params for simulation
        self.coins_to_invest = self.df_simulation['coins_to_invest_in'].iloc[
            0]  # Coin to invest in - if Consts.ALL then invest in all coins in mlresults
        self.tick_time_hours = params[2]  # The time to tick for simulation in hours
        self.fees = params[3]  # The fees class which includes individual fees and default fees
        self.capital_history = pd.DataFrame(
            data={'date_time': [], 'liquid_capital': [], 'shorts_capital': [], 'long_capital': [],
                  'leverage_capital': [], 'fees_paid': [], 'miss_positions': [], 'hit_positions': [],
                  'stopped_positions': [], 'expired_positions': [], 'hit_trail_positions': [],
                  'total_number_of_active_positions': [], 'hours_with_no_predictions': []
                  })  # Will be updated after every tick
        self.start_running_time = params[4]  # The start of the running time
        self.time_ticker = None  # Will be initiated at the run function as a class
        self.coins_for_benchmark = params[5]  # The requested benchmarks
        self.hours_with_no_predictions = 0

        # start running simulation
        self.run()

    def run(self):
        """
        Runs simulation with the following order:
        0. Updates all run according to new time.
        1. Apply hourly fees if exist
        2. Check if positions reached the high or low target and close/trail them accordingly
        3. Check if positions expired and close accordingly
        4. Apply active positions strategy on all open positions and close accordingly
        5. Check if there are new MLResults and invest accordingly

        At the end of the run, creates 3 files for each simulation and 1 file which aggregates all together: ( path = /opt/simulation
        a. capital_history.csv - the status of the portfolio every tick time.
        b. positions.csv - all the positions for the simulation.
        c. simulation.csv - documentation of all params of the simulation.
        :return:
        """

        logger.info('Starting simulation ID: {}'.format(self.df_simulation.index[0]))

        # Start time is according to oldest ML result
        start_timestamp, end_timestamp = self.simulation_time_interval()

        # Create a time ticker for simulation
        self.time_ticker = TimeTicker.TimeTicker(start_timestamp, self.tick_time_hours)

        # Initial Portfolio
        active_portfolio = Portfolio.Portfolio(self.df_simulation, self.fees, self.time_ticker)

        # Loop according to tick time, while there are still positions open or while there are still MLResults left to iterate
        while self.time_ticker.current_time < end_timestamp:

            # Update portfolio according to new time for next round
            active_portfolio.updater(Consts.UPDATES_NEW_TIME_IS_LIQUIDATE)

            # If There are leveraged positions, decrease fees
            active_portfolio.apply_time_leverage_fees()

            # If active positions, update them
            if active_portfolio.is_there_open_positions():
                active_portfolio.updater(Consts.REACH_TARGET_UPDATE)
                active_portfolio.updater(Consts.IS_EXPIRED)

            # Fetch ml results for
            current_ml_results = self.ml_results_df.loc[
                self.ml_results_df['prediction_time'] == self.time_ticker.current_time]

            if len(current_ml_results) == 0:
                self.hours_with_no_predictions += 1

            # Filter according to coin_to_invest
            if self.coins_to_invest[0] != Consts.ALL:
                current_ml_results = current_ml_results.loc[
                    self.ml_results_df['coin_symbol'].isin(self.coins_to_invest)]

            # If there is MLResult in current time
            if len(current_ml_results) > 0:
                active_portfolio.updater(Consts.IS_ACTIVE_INVEST_STRATEGY, ml_results=current_ml_results)
                active_portfolio.enter_new_positions(current_ml_results)

            # Update capital history
            self.capital_history = self.capital_history.append(pd.DataFrame(
                data={'date_time': [TimeHelper.epoch_to_date_time(self.time_ticker.current_time)],
                      'liquid_capital': [active_portfolio.liquid_capital],
                      'shorts_capital': [active_portfolio.short_capital],
                      'long_capital': [active_portfolio.long_capital],
                      'leverage_capital': [active_portfolio.leverage_capital],
                      'fees_paid': [active_portfolio.fees_paid],
                      'miss_positions': [active_portfolio.miss_positions],
                      'hit_positions': [active_portfolio.hit_positions],
                      'stopped_positions': [active_portfolio.stopped_positions_counter],
                      'expired_positions': [active_portfolio.expired_positions_counter],
                      'hit_trail_positions': [active_portfolio.hit_trail_positions],
                      'hours_with_no_predictions': [self.hours_with_no_predictions],
                      'total_number_of_active_positions': [
                          len(active_portfolio.active_long_positions + active_portfolio.active_short_positions)]
                      }), ignore_index=True, sort=True)

            # Advance current_timestamp
            self.time_ticker.advance_one_step()

        # Closing all open positions
        if active_portfolio.is_there_open_positions():
            logger.info("There are open positions, closing all")
            active_portfolio.updater(Consts.FORCE_CLOSE_ALL_POSITIONS)

        logger.info('Creating analytics file for simulation ID: {}'.format(self.df_simulation.index[0]))
        positions_history = self.fetch_positions_history_df(active_portfolio)
        AnalyticsFactory.start(self.start_running_time, self.coins_for_benchmark, self.df_simulation, positions_history,
                               self.capital_history)

        logger.info('end of simulation ID: {}'.format(self.df_simulation.index[0]))
        # TODO: send to analytics factory and the write posion_history,capital history and and stats

    def simulation_time_interval(self):
        """
        according to ml_results_df oldest and latest date
        :return: start_timestamp, end_timestamp
        """

        return self.ml_results_df['prediction_time'].min(), self.ml_results_df['prediction_time'].max()

    def fetch_positions_history_df(self, active_portfolio):
        """
        creates a df of all the positions in the simulation
        :param active_portfolio:
        :return: df of positions histroy
        """

        positions_history = pd.DataFrame(
            data={'initial_time': [], 'end_time': [], 'coin_symbol': [], 'order_type': [], 'life_time_in_hours': [],
                  'positive_target': [], 'negative_target': [],
                  'initial_capital_include_leverage': [], 'final_capital': [], 'buy_price': [], 'last_price': [],
                  'hit_profit_target': [],
                  'hit_loss_target': [], 'expired': [], 'stopped': [], 'liquidated': [],
                  'trailing_activated': [], 'hours_position_open': [], 'fees_paid': [], 'leverage_capital': [],
                  'leverage': [], 'ROI': []})
        for pos in active_portfolio.closed_long_positions + active_portfolio.closed_short_positions:
            positions_history = positions_history.append(pd.DataFrame(
                data={'initial_time': [TimeHelper.epoch_to_date_time(pos.initial_time)],
                      'end_time': [TimeHelper.epoch_to_date_time(pos.position_end_time)],
                      'coin_symbol': [pos.coin_symbol],
                      'order_type': [pos.order_type], 'life_time_in_hours': [pos.initial_position_life_time],
                      'positive_target': [pos.positive_target], 'negative_target': [pos.negative_target],
                      'initial_capital_include_leverage': [pos.initial_capital], 'final_capital': [pos.current_capital],
                      'buy_price': [pos.buy_price],
                      'last_price': [pos.last_price],
                      'hit_profit_target': [pos.hit_profit_target], 'hit_loss_target': [pos.hit_loss_target],
                      'expired': [pos.expired], 'stopped': [pos.stopped], 'liquidated': [pos.liquidated],
                      'trailing_activated': [pos.trailing_activated], 'hours_position_open': [pos.hours_position_open],
                      'fees_paid': [pos.fees_paid], 'leverage_capital': [pos.leverage_capital],
                      'leverage': [pos.leverage], 'ROI': [pos.get_roi_status()]}), ignore_index=True, sort=True)
        return positions_history

    def calculate_benchmark(self, field_date_time, coin_benchamrk, first_value_price, amountOfCapital):
        """
        for function get benchmarks calculate benchmark
        :param x:
        :param coin_benchamrk:
        :param first_value_price:
        :param amountOfCapital:
        :return:
        """
        status, coin_data = data_helper.get_coin_data(field_date_time, coin_benchamrk)
        # todo throw logger error
        if not status:
            logger.error("get find key: {} in reddis".format(str(field_date_time) + '__' + coin_benchamrk))
            exit(1)
        row_price = coin_data['_open']
        benchmark = float(row_price) / float(first_value_price) * float(amountOfCapital)
        return benchmark

    def add_benchmarks(self, capital_history, symbols_list, amountOfCapital):
        """
        add column to result with benchmark coins
        :param capital_history:
        :param amountOfCapital
        :return:
        """

        # capital_history = pd.DataFrame(
        #     data={'date_time': ['1483228800', '1483232400', '1483236000', '1483239600'],
        #           'liquid_capital': [123, 213, 342, 44324], 'shorts_capital': [213, 3213, 3123, 4234],
        #           'long_capital': [1323, 21312, 4324, 4234]})
        # load_time_start = datetime.datetime(year=2017, month=1, day=1)
        # _DataHelper.init_data_first_time(['BTC', 'ETH'], TimeHelper.datetime_to_epoch(load_time_start))
        capital_history = capital_history.sort_values(by=['date_time'])
        amountOfCapital = 1000
        temp = {}
        for coin_benchamrk in symbols_list:
            status, result = data_helper.get_coin_data(capital_history['date_time'].values[0],
                                                       coin_benchamrk)
            # todo throw logger error
            if not status:
                exit(1)
            first_value_price = result['_open']
            new_col_name = 'benchmark_' + coin_benchamrk
            capital_history[new_col_name] = capital_history['date_time'].apply(
                lambda x: self.calculate_benchmark(x, coin_benchamrk, first_value_price, amountOfCapital))
