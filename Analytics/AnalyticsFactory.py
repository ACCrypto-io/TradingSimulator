import numpy as np
import logging

from Utilities import Consts
from Utilities.DataHelper import DataHelper
import pandas as pd
import os
from Utilities import TimeHelper

logger = logging.getLogger("Analytics Factory")

# risk free rate represents us.treasury bill. need to be update every according to time interval change  - https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield
risk_free_rate = 0.005

_data_helper = DataHelper()


def start(start_running_time, coins_for_benchmark, df_simulation, positions_history, capital_history):
    """
    function "get statistics" was build before in version one. and this function arrange the dataframe to
    be sent to "get statistics" correctly. acc = [{date_time,capital},..],benchmark = [{date_time,capital},..]
    :param simulation_result_with_benchmark: dataframe with acc capital and benchmarks capital example pd.DataFrame(
    #     data={'date_time': ['1483228800', '1483232400', '1483236000', '1483239600'],
    #           'capital': [123, 213, 342, 44324], 'benchmark_BTC': [222, 222, 222, 222],
    :return: dataframe {'subject': ['ACC-BTC', 'ACC-ETH'],
    #                 'alpha': [123, 213, 342, 44324], 'betta': [222, 222, 222, 222],
    #                 'benchmark_ETH': [222, 222, 222, 222], 'rsquared': [222, 222, 222, 222],
    """
    # simulation_result_with_benchmark = pd.DataFrame(
    #     data={'date_time': ['1483228800', '1483232400', '1483236000', '1483239600'],
    #           'capital': [123, 213, 342, 44324], 'benchmark_BTC': [222, 222, 222, 222],
    #           'benchmark_ETH': [222, 222, 222, 222]})
    # final_result1 = {'subject': ['ACC-BTC', 'ACC-ETH'],
    #                 'alpha': [123, 213, 342, 44324], 'betta': [222, 222, 222, 222],
    #                 'benchmark_ETH': [222, 222, 222, 222], 'rsquared': [222, 222, 222, 222],
    #                 'standard_deviation': [222, 222, 222, 222], 'sharp_ratio': [222, 222, 222, 222]}

    path = os.path.join(Consts.PATH_TO_WRITE_RESULT,
                        TimeHelper.epoch_to_date_time(start_running_time).strftime(Consts.WRITE_DATE_FORMAT),
                        str(df_simulation.index[0]))
    os.makedirs(path, exist_ok=True)

    positions_history.to_csv(os.path.join(path, 'positions.csv'), index=False)
    df_simulation.index.names = ['simulation_id']
    df_simulation.to_csv(os.path.join(path, 'simulation.csv'))
    capital_history['date_time'] = pd.to_datetime(capital_history['date_time'], format=Consts.READ_DATE_FORMAT).apply(
        lambda x: TimeHelper.datetime_to_epoch(x))
    capital_history['capital'] = capital_history['liquid_capital'] + capital_history['shorts_capital'] + \
                                 capital_history['long_capital']

    # acc_capital = capital_history.drop(capital_history.columns.difference(['capital', 'date_time']), 1).to_dict(
    #     'record')
    acc_capital_with_banchmark_df, benchmark_column_names = add_benchmarks(capital_history, coins_for_benchmark,
                                                                           df_simulation['amount_of_capital'].iloc[0])

    acc_capital_with_banchmark_df['date_time'] = acc_capital_with_banchmark_df['date_time'].apply(
        lambda x: TimeHelper.epoch_to_date_time(x))
    acc_capital_with_banchmark_df.set_index('date_time', inplace=True)
    acc_capital_with_banchmark_df.sort_index(inplace=True)
    acc_capital_with_banchmark_df.to_csv(os.path.join(path, 'capital_history.csv'))

    analytics_result_list = []
    for column_benchmark in benchmark_column_names:
        temp_obj = get_statistics(df_simulation.index[0], 'ACC-{}'.format(column_benchmark),
                                  acc_capital_with_banchmark_df['capital'].values,
                                  acc_capital_with_banchmark_df[column_benchmark].values)
        analytics_result_list.append(temp_obj)

    analytics_result_df = pd.DataFrame(
        data=analytics_result_list)
    analytics_result_df['ACC_ROI'] = (acc_capital_with_banchmark_df['capital'].values[-1] /
                                      acc_capital_with_banchmark_df['capital'].values[0]) - 1

    last_row_capital_history = capital_history.tail(1).copy()
    last_row_capital_history['simulation_id'] = df_simulation.index[0]

    last_row_capital_history.set_index(['simulation_id'], inplace=True)
    analytics_result_df.set_index(['simulation_id'], inplace=True)

    analytics_result_df = analytics_result_df.join(df_simulation).join(last_row_capital_history)

    path_to_analytics = os.path.join(Consts.PATH_TO_WRITE_RESULT,
                                     TimeHelper.epoch_to_date_time(start_running_time).strftime(
                                         Consts.WRITE_DATE_FORMAT), 'analytics')

    os.makedirs(path_to_analytics, exist_ok=True)
    path_to_create_result = os.path.join(path_to_analytics, 'Simulation__{}__Analytics.csv'.format(df_simulation.index[0]))
    analytics_result_df.to_csv(path_to_create_result , index=True)
    logger.info('Finish creating analytics file for simulation ID: {}, you can look in: {}'.format(df_simulation.index[0], path_to_create_result))

def get_statistics(simulation_id, subject, acc_storyline, benchmark_storyline):
    """

    :param acc_storyline:
    :param benchmark_storyline:
    :return: {'alpha': alpha, 'beta': beta, 'rsquared': rsquared, 'standard_deviation': standard_deviation,
            'sharp_ratio': sharp_ratio}
    """

    # acc storyline       = {'capital': capital, 'date_time': current_time}
    # benchmark_storyline = {'capital': capital, 'date_time': current_time}

    # acc storyline = [capital1,capital2,capital3]
    # benchmark_only_price = [capital1, capital2, capital3]
    acc_prices_percentage_change = arrange_by_percentage_change(acc_storyline)
    benchmark_prices_percentage_change = arrange_by_percentage_change(benchmark_storyline)
    # acc storyline = [capital1%,capital2%,capital3%]
    # benchmark_only_price = [capital1%, capital2%, capital3%]
    beta = _beta(benchmark_prices_percentage_change, acc_prices_percentage_change)
    alpha = _alpha(benchmark_storyline, acc_storyline, beta)
    rsquared = _rsquared(benchmark_storyline, acc_storyline)
    standard_deviation = _standard_deviation(acc_prices_percentage_change)
    sharp_ratio = _sharp_ratio(acc_prices_percentage_change, standard_deviation)

    return {'simulation_id': simulation_id, 'subject': subject, 'alpha': alpha, 'beta': beta, 'rsquared': rsquared,
            'standard_deviation': standard_deviation,
            'sharp_ratio': sharp_ratio}


def _arrange_by_percentage_change_v2(benchmark_prices):
    counter = 0
    yesterday_price = 0
    new_change_prices = {}
    for row in benchmark_prices:
        if counter == 0:
            new_change_prices[row] = 0
            yesterday_price = benchmark_prices[row]
            counter += 1
            continue

        change = benchmark_prices[row] / yesterday_price
        new_change_prices[row] = change
        yesterday_price = benchmark_prices[row]
        counter += 1
    return new_change_prices


def arrange_by_percentage_change(prices):
    first_read = True
    yesterday_price = 0
    new_change_array = []
    for price in prices:
        if first_read:
            new_change_array.append(0)
            yesterday_price = price
            first_read = False
            continue
        # if yesterday_price == 0 or price == 0:
        #     change = 0
        #     new_change_array.append(change)
        #     yesterday_price = price
        #     counter += 1
        else:
            change = (price - yesterday_price) / yesterday_price
            if abs(change) > 20:
                logger.error("Change is not make any sense (taking the change from yesterday)...")
                new_change_array.append(new_change_array[-1])
            else:
                new_change_array.append(change)
                yesterday_price = price

    return new_change_array


# takes the last price of benchmark and acc and calculates the alpha for the whole period of time in the csv file.
def _alpha(benchmark_prices, acc_prices, beta):
    last_benchmark_price = (benchmark_prices[-1] - benchmark_prices[0]) / benchmark_prices[0]
    last_acc_price = (acc_prices[-1] - acc_prices[0]) / acc_prices[0]
    alpha = last_acc_price - risk_free_rate - beta * (last_benchmark_price - risk_free_rate)
    return alpha


def _beta(benchmark_prices_percentage_change, acc_prices_percentage_change):
    np_benchmark_array = np.array(benchmark_prices_percentage_change)
    np_acc_array = np.array(acc_prices_percentage_change)
    mean_acc = np.mean(np_acc_array)
    mean_benchmark = np.mean(np_benchmark_array)

    # covarriance calculation
    sum = 0
    for benchmark_change, acc_change in zip(benchmark_prices_percentage_change, acc_prices_percentage_change):
        sum += ((acc_change - mean_acc) * (benchmark_change - mean_benchmark))
    cov = sum / (len(benchmark_prices_percentage_change) - 1)
    var = np.var(np_acc_array)
    beta = cov / var
    return beta


def _rsquared(benchmark_prices, acc_prices):
    mean_acc = np.mean(acc_prices)
    mean_benchmark = np.mean(benchmark_prices)

    # Finding the line of best fit
    denominator = 0.0
    numerator = 0.0
    for benchmark_change, acc_change in zip(benchmark_prices, acc_prices):
        numerator += (acc_change - mean_acc) * (benchmark_change - mean_benchmark)
        denominator += ((acc_change - mean_acc) ** 2)
    m = numerator / denominator
    b = mean_benchmark - (m * mean_acc)

    # predicted acc price value
    predicted_price = []
    for point in acc_prices:
        predicted_point = (point * m) + b
        predicted_price.append(predicted_point)

    # substract the actual price from the predicted and square result
    prediction_error = []
    sum_errors = 0.0

    for prediction, real_price in zip(predicted_price, benchmark_prices):
        new_point = (prediction - real_price) ** 2
        prediction_error.append(new_point)
        sum_errors += new_point

    average_error = sum_errors / len(benchmark_prices)
    second_sum = 0.0
    for pred_error in prediction_error:
        second_sum += ((pred_error - average_error) ** 2)

    return 1 - (sum_errors / second_sum)


def _standard_deviation(acc_change):
    np_acc_array = np.array(acc_change)
    average_acc = np.average(np_acc_array)
    sum_st = 0.0

    for change in acc_change:
        sum_st += ((average_acc - change) ** 2)

    standard_deviation = np.sqrt(sum_st / (len(acc_change) - 1))
    return standard_deviation


def _sharp_ratio(acc_prices_percentage_change, standard_deviation):
    np_acc_array = np.array(acc_prices_percentage_change)
    mean = np.mean(np_acc_array)

    if standard_deviation == 0:
        standard_deviation = 0.00001

    sharp_ratio = (mean - risk_free_rate) / standard_deviation

    return sharp_ratio


def calculate_benchmark_for_single_coin(field_date_time, coin_benchamrk, first_value_price, amountOfCapital):
    """
    for function get benchmarks calculate benchmark
    :param x:
    :param coin_benchamrk:
    :param first_value_price:
    :param amountOfCapital:
    :return:
    """
    status, coin_data = _data_helper.get_coin_data(field_date_time, coin_benchamrk)
    if not status:
        logger.error("get find key: {} in reddis".format(str(field_date_time) + '__' + coin_benchamrk))
        exit(1)
    row_price = coin_data['_open']
    benchmark = float(row_price) / float(first_value_price) * float(amountOfCapital)
    return benchmark


def calculate_benchmark_for_per_coins(field_date_time, list_coins_to_benchmark, first_value_price_average,
                                      amountOfCapital):
    """
    for function get benchmarks calculate benchmark for pers
    :param x:
    :param coin_benchamrk:
    :param first_value_price:
    :param amountOfCapital:
    :return:
    """
    sum_coins_prices_btc = 0
    for coin_to_benchmark in list_coins_to_benchmark:
        status, coin_data = _data_helper.get_coin_data(field_date_time, coin_to_benchmark)
        if not status:
            logger.error("get find key: {} in reddis".format(str(field_date_time) + '__' + coin_to_benchmark))
            exit(1)
        sum_coins_prices_btc += float(coin_data['_open'])

    price_average = sum_coins_prices_btc / len(list_coins_to_benchmark)
    benchmark = float(price_average) / float(first_value_price_average) * float(amountOfCapital)
    return benchmark


def add_benchmarks(capital_history, symbols_list, amountOfCapital):
    """
    add column to result with benchmark coins
    :param capital_history:
    :param amountOfCapital
    :return:
    """

    capital_history.sort_values(by=['date_time'], inplace=True)
    benchmark_column_names = []
    for coin_or_list_benchmark in symbols_list:
        sum_coins_prices_btc = 0
        for coin_benchmark in coin_or_list_benchmark:
            status, result = _data_helper.get_coin_data(capital_history['date_time'].values[0],
                                                        coin_benchmark)
            if not status:
                logger.error("error in request, key: {}__{}".format(str(capital_history['date_time'].values[0]),
                                                                           coin_or_list_benchmark))
                exit(0)
            sum_coins_prices_btc += float(result['_open'])
        first_value_price_average = sum_coins_prices_btc / len(coin_or_list_benchmark)
        new_col_name = 'benchmark_' + '__'.join(str(e) for e in coin_or_list_benchmark)
        benchmark_column_names.append(new_col_name)
        capital_history[new_col_name] = capital_history['date_time'].apply(
            lambda x: calculate_benchmark_for_per_coins(x, coin_or_list_benchmark, first_value_price_average,
                                                        amountOfCapital))

    return capital_history, benchmark_column_names


if __name__ == "__main__":
    acc = [100, 150, 200, 300, 400]
    bench = [100, 150, 200, 300, 400]
    acc_change = arrange_by_percentage_change(acc)
    bench_change = arrange_by_percentage_change(bench)
    print(acc_change)
    print(bench_change)

    cov = np.cov(np.array([acc_change, bench_change]))[0][0]
    print(cov)
    beta_res = cov / np.var(acc_change)
    print(beta_res)
    print(_beta(bench_change, acc_change))
    # start()
# get_acc_benchmark([1000])
# # start_time = datetime.datetime.strptime("2018-01-02", Consts.TIME_FORMAT)
# start_time = datetime.datetime.now()
#
# #get raw data
# benchmark_prices = []
# acc_prices = []
# with open('acc_vs_benchmark.csv', 'rb') as csvfile:
#     load_data = csv.DictReader(csvfile)
#     for line in load_data:
#         benchmark_prices.append(float(line['benchmark']))
#         acc_prices.append(float(line['acc']))
#
# benchmark_prices_percentage_change = arrange_by_percentage_change(benchmark_prices)
# acc_prices_percentage_change = arrange_by_percentage_change(acc_prices)
# beta = beta(benchmark_prices_percentage_change, acc_prices_percentage_change)
# alpha = alpha(benchmark_prices, acc_prices,beta)
# rsquared = rsquared(benchmark_prices, acc_prices)
# standard_deviation = standard_deviation(acc_prices)
# sharp_ratio = sharp_ratio(acc_prices_percentage_change, standard_deviation)
#
# print 'Alpha: ', alpha
# print 'Beta: ', beta
# print 'Rsquared: ', rsquared
# print 'Standard Deviation: ', standard_deviation
# print 'Sharp Ratio: ', sharp_ratio
# print "Finish"
