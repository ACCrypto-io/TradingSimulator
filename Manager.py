import argparse
import datetime
import os
import logging

import pandas as pd

from Utilities import TimeHelper, Consts
import FindBestStrategy

# Ignore SettingWithCopyWarning
pd.options.mode.chained_assignment = None


def benchmark_handler(_str_coins):
    _str_coins = _str_coins.upper()
    coins_benchmark = []
    for _coins in _str_coins.split(' '):
        if _coins == '':
            continue
        coins_benchmark.append(_coins.split(','))
    return coins_benchmark


logger = logging.getLogger("Manager")
parser = argparse.ArgumentParser()
parser.add_argument("-RunSimulations", type=bool, nargs='?',
                    const=True, default=None,
                    help="run simulations according to files 1. simulationparams 2. MLResult 3. "
                         "Const(running params). 3. individual Fees.")

parser.add_argument("-pathToCoinsPrice", type=str, nargs='?',
                    const=True, default=None,
                    help="Full path to a csv with coins prices. please see README.md for further information.")

parser.add_argument("-benchmarkCoins", type=benchmark_handler, nargs='?',
                    const=True, default=[['BTC']],
                    help="The coin/coins for benchmark, for 2 benchmarks for BTC and ETH write \"BTC ETH\", "
                         "for 1 benchmark of BTC and ETH (new index) write \"BTC,ETH\". default: \"BTC\".")

parser.add_argument("-resultPath", type=str, nargs='?',
                    const=True, default=os.getcwd(),
                    help="The path to create the results folder. default the working dir.")

parser.add_argument("-AnalyzeExistingResults", type=bool, nargs='?',
                    const=True, default=None,
                    help="take the result of the simulation that already finished. and summarizes it.")

args = parser.parse_args()

if __name__ == '__main__':
    current_time = TimeHelper.current_time_stamp()
    Consts.BENCHMARKS = args.benchmarkCoins
    Consts.set_path_to_write_result(args.resultPath)
    if not args.RunSimulations and not args.AnalyzeExistingResults:
        print("Please select at least one runStage in order to start Manager.")
        quit(1)

    if args.RunSimulations:
        if args.pathToCoinsPrice is None:
            print("Please specify the pathToCoinsPrice.")
            quit(1)
        if not os.path.isfile(args.pathToCoinsPrice):
            print("pathToCoinsPrice does not exist {}.".format(args.pathToCoinsPrice))
            quit(1)
        if not args.pathToCoinsPrice.endswith('.csv.gz'):
            print("pathToCoinsPrice must be csv and gzip compressed.")
            quit(1)
        FindBestStrategy.run(args.pathToCoinsPrice, benchmark_symbols_list=Consts.BENCHMARKS)

    elif args.AnalyzeExistingResults:
        # Remove files from old runs in Consts.PATH_TO_WRITE_PARTIAL_RESULT
        logger.info("Remove files from old runs in {}".format(Consts.PATH_TO_WRITE_PARTIAL_RESULT))
        files_from_past_runs = list(filter(lambda x: x[0] != '.', os.listdir(Consts.PATH_TO_WRITE_PARTIAL_RESULT)))
        for file_name in files_from_past_runs:
            if 'Simulations_Partial_Analytics__' in file_name:
                os.remove(os.path.join(Consts.PATH_TO_WRITE_PARTIAL_RESULT, file_name))

        # Find last run directory analytics result
        logger.info("Find last run directory analytics result")
        current_time = TimeHelper.current_time_stamp()
        path_to_analytics = Consts.PATH_TO_WRITE_RESULT
        max_date = datetime.datetime(1970, 1, 1)
        max_str_date = ''
        path_project_result_dir = list(filter(lambda x: x[0] != '.', os.listdir(path_to_analytics)))
        for file_name in path_project_result_dir:
            try:
                file_name_date = datetime.datetime.strptime(file_name, Consts.WRITE_DATE_FORMAT)
            except ValueError:
                logger.warning('Fail to read file {}'.format(file_name))
                continue
            if file_name_date > max_date:
                max_str_date = file_name
        # Concat result
        path_last_run_analytics = os.listdir(os.path.join(path_to_analytics, max_str_date, 'analytics'))
        list_last_run_analytics_files_dfs = []
        for file_name in path_last_run_analytics:
            full_file_path = os.path.join(path_to_analytics, max_str_date, 'analytics', file_name)
            if 'Simulations__Summery__Analytics' in file_name:
                logger.info("Full Summary is already existing in path: {}".format(full_file_path))
                quit(1)
            list_last_run_analytics_files_dfs.append(pd.read_csv(full_file_path))

        all_analytics_files_df = pd.concat(list_last_run_analytics_files_dfs, ignore_index=True, sort=True)
        # Create partual summery
        path_to_create_partial_result = os.path.join(Consts.PATH_TO_WRITE_PARTIAL_RESULT,
                                                     'Simulations_Partial_Analytics__{}.csv'.format(max_str_date))
        all_analytics_files_df.set_index('simulation_id', inplace=True)
        all_analytics_files_df.to_csv(
            os.path.join(Consts.PATH_TO_WRITE_PARTIAL_RESULT,
                         'Simulations_Partial_Analytics__{}.csv'.format(max_str_date)))
        logger.info("Finished create partial summery result, path: {}".format(path_to_create_partial_result))


