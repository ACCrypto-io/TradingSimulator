import os
import pandas as pd
import numpy as np

from Utilities import Consts
from Utilities.SimulationParams import SimulationParamsOptions
import itertools
from Utilities.DataHelper import DataHelper
from Utilities import TimeHelper

_data_helper = DataHelper()


def load_ml_results(path, order_type):
    """
    Loads MLResults into a dataframe
    :return: df of MLResults
    """
    MLResult_files = os.listdir(path)
    list_MLResult = []
    for file_name in MLResult_files:
        list_MLResult.append(pd.read_csv(path + file_name))

    all_MLResult_df = pd.concat(list_MLResult, ignore_index=True, sort=True)

    all_MLResult_df['order_type'] = order_type
    return all_MLResult_df


def load_simulation_params():
    """
    Loads Utilities/SimulationParams
     get all params from simulation params file.
    and create dataframe with all the combinations that can be.
    :return:
    """
    temp_obj = SimulationParamsOptions()
    list_of_params = []
    simulations_params_names = []
    for att in dir(temp_obj):
        if att[:2] == '__':
            continue
        param_value = getattr(temp_obj, att)
        if len(param_value) == 0:
            continue
        simulations_params_names.append(att.lower())
        list_of_params.append(param_value)

    data = list(itertools.product(*list_of_params))
    all_simulation_options_df = pd.DataFrame.from_records(data, columns=simulations_params_names)
    return all_simulation_options_df


def get_list_coins_unique(df1, df2):
    new_df = pd.concat([df1.coin_symbol, df2.coin_symbol], ignore_index=True, sort=True)
    return list(set(new_df))


def convert_dfs_int_to_float(array_of_df):
    """
    because dataframe convert some of the numbers in csv files to int.
    and we needed float. so this is convert int column to float

    :param array_of_df:
    :return:
    """
    for _df in array_of_df:
        for column in _df:
            if _df[column].dtype == int:
                _df[column] = _df[column].apply(pd.to_numeric(float))


def fetch_simulations(benchmark_symbols_list, path_to_data_file):
    """
    init coins data to redis
    Creates 3 dataframe 1.MLResult. 2.all simulation params options. 3. fees
    a data frame with index as simulation_id and the following columns:
    [amount_of_capital, max_percante_cap_invested_in_a_round, max_percentage_out_of_volume,
    :return: params, ml_results, prices
    """
    # benchmark_symbols_list, can be list in a list so this how i'm init all coins data to redis
    list_coins_to_init = []
    for temp_obj in benchmark_symbols_list:
        if not isinstance(temp_obj, list):
            list_coins_to_init.append(temp_obj)
            continue
        list_coins_to_init += temp_obj

    ml_results = pd.concat([load_ml_results(Consts.ML_RESULT_LONG_PATH, Consts.LONG),
                            load_ml_results(Consts.ML_RESULT_SHORT_PATH, Consts.SHORT)], ignore_index=True, sort=True)

    ml_results['prediction_time'] = pd.to_datetime(ml_results['prediction_time'], format=Consts.READ_DATE_FORMAT).apply(
        lambda x: TimeHelper.datetime_to_epoch(x))
    simulations_options_df = load_simulation_params()

    _data_helper.init_data(list(set(list_coins_to_init).union(set(ml_results.coin_symbol))), path_to_data_file,
                           ml_results['prediction_time'].min(), ml_results['prediction_time'].max())

    convert_dfs_int_to_float([ml_results, simulations_options_df])
    return [ml_results, simulations_options_df]


if __name__ == '__main__':
    pass
