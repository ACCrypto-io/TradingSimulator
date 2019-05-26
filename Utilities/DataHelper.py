import logging

import pandas as pd
from Utilities import Consts
from Utilities import TimeHelper

logger = logging.getLogger("DataGetter")


class DataHelper(object):

    class __DataHelper:
        def __init__(self):
            self.__df = None

        def init_data(self, symbols_list, path_to_data_file, start_date, end_date, compression='gzip'):
            df_data = pd.read_csv(path_to_data_file, compression=compression)
            diff_col = Consts.COINS_CANDLE_STICK_HEADERS - set(df_data.columns)
            if len(diff_col) > 0:
                logger.error("There are missing columns in candle stick info, headers: {}".format(diff_col))
                quit(1)

            df_data.set_index([Consts.COIN_SYMBOL, Consts.TIME_COLUMN_PRICE], inplace=True)

            # Leaving only coins that are going to be predict
            idx = pd.IndexSlice
            self.__df = df_data.loc[idx[symbols_list, :]]  # type: pd.DataFrame

            for coin_symbol, df_group in self.__df.reset_index().groupby(Consts.COIN_SYMBOL):
                min_time, max_time = df_group[Consts.TIME_COLUMN_PRICE].min(), df_group[Consts.TIME_COLUMN_PRICE].max()
                if min_time > start_date or max_time < end_date:
                    logger.error("Missing data for coin {} (in data: min time {}, max time {}, "
                                 "in predictions: min time {}, max time {})"
                                 .format(coin_symbol, min_time, max_time, start_date, end_date))
                    quit(1)

        def get_coin_data(self, ptime, symbol):
            """
            coin data from redis by ptime and symbol
            :param ptime:string
            :param symbol:
            :return:
            """
            if self.__df is None:
                raise Exception('Please call init_data before using get_coin_data')

            try:
                return True, self.__df.loc[symbol, ptime]
            except KeyError as e:
                logger.warning("(KeyError) There is no {} for {} (human date {}), error: {}"
                               .format(symbol, ptime, TimeHelper.epoch_to_date_time(ptime), e))
                return False, []
            except TypeError as e2:
                logger.warning("(TypeError) There is no {} for {} (human date {}), error: {}"
                               .format(symbol, ptime, TimeHelper.epoch_to_date_time(ptime), e2))
                return False, []

    instance = None

    # Used for singleton
    def __new__(cls):  # __new__ always a classmethod
        if not DataHelper.instance:
            DataHelper.instance = DataHelper.__DataHelper()
        return DataHelper.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)


if __name__ == '__main__':
    pass
    # DataHelper =DataHelper()
    # start_time = time.time()
    # DataHelper.init_data_first_time(1483228800, 1514764800)
    # end_time = time.time()
    # print(start_time)
    # print(end_time)
    # print(end_time - start_time)
