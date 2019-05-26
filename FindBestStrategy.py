import multiprocessing
import os

import logging
import pandas as pd
from Utilities import LoaderHelper, TimeHelper, Consts
from Simulation import Simulation
from Fees import Fees
from tqdm import tqdm
import os.path

logger = logging.getLogger("FindBestStrategy")


def run(path_to_data_file, current_time=TimeHelper.current_time_stamp(), tick_time_hours=Consts.TICK_TIME_HOURS,
        benchmark_symbols_list=None):
    """
    1) fetch data from files - 1.a. simulation params 1.b. fees 1.c. ml result
    2) run multiprocess all simulation
    3) concate all result(analytics) files from simulation.
    :param id:
    :param tick_time_hours:
    :param benchmark_symbols_list:
    :return:
    """
    if benchmark_symbols_list is None:
        benchmark_symbols_list = [['BTC']]
    # Anlayze results
    logger.info("Getting alto results")
    df_ml_results, df_simulations = LoaderHelper.fetch_simulations(benchmark_symbols_list, path_to_data_file)
    _fees = Fees.Fees()

    # Multi proccesing to run simulation classes which writes results into Simulator/Results/{id}
    data_for_run = []
    df_simulations.index.names = ['index']
    gb = df_simulations.groupby('index')
    for _df in [gb.get_group(x) for x in gb.groups]:
        data_for_run.append((df_ml_results, _df, tick_time_hours, _fees, current_time, benchmark_symbols_list))

    pbar = tqdm(total=len(data_for_run))

    def print_progress(res):
        pbar.update()

    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        print(data_for_run)
        res = [p.apply_async(Simulation.Simulation, args=(_single_run,), callback=print_progress) for _single_run in
               data_for_run]
        for func_res in res:
            func_res.get()
        p.close()
        p.join()
    pbar.close()

    path_to_analytics = os.path.join(Consts.PATH_TO_WRITE_RESULT, TimeHelper.epoch_to_date_time(
        current_time).strftime(
        Consts.WRITE_DATE_FORMAT), 'analytics')

    analytics_files = os.listdir(path_to_analytics)
    list_analytics_files_dfs = []
    for file_name in analytics_files:
        list_analytics_files_dfs.append(pd.read_csv(os.path.join(path_to_analytics, file_name)))

    all_analytics_files_df = pd.concat(list_analytics_files_dfs, ignore_index=True, sort=True)
    path_to_write_summery = os.path.join(path_to_analytics, 'Simulations__Summery__Analytics.csv')
    all_analytics_files_df.set_index('simulation_id', inplace=True)
    all_analytics_files_df.to_csv(path_to_write_summery)
    logger.info('Finished all simlations, base path result:{}, analytics summery: {}'.format(os.path.join(Consts.PATH_TO_WRITE_RESULT, TimeHelper.epoch_to_date_time(
        current_time).strftime(
        Consts.WRITE_DATE_FORMAT)), path_to_write_summery))
