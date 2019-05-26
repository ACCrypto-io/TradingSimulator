import os
import logging
import sys

# ------------------ Set Logging format ------------------ #
LOGGING_FORMAT = "%(levelname)-8s %(module)-22s:%(lineno)-4s %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT, stream=sys.stdout)

# ------------------ DB ------------------ #
DB_NAME = 'alto_db'

# ------------------ REPLACE TXT FOR SQL ------------------ #
REPLACE_TXT_S1 = '%REPLACE_TXT_S1%'
REPLACE_TXT_S2 = '%REPLACE_TXT_S2%'
REPLACE_TXT_S3 = '%REPLACE_TXT_S3%'

# ------------------ BANCH-SPLICES FOR SQL --------------------- #
BATCH_AMOUNT_SELECT = 2000

# ------------------ CONVERT_TIME --------------------- #
READ_DATE_FORMAT = "%Y-%m-%dT%H"
WRITE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

# ------------------ OTHER ------------------ #
col_data_coins_db_name = 'ptime_and_symbol'
LONG = 'long'
SHORT = 'short'
ALL = 'All'
NUM_OF_CLASSES = 3
FULLY_INVESTED = 'fully_invested'
CAPITAL_TO_INVEST = 'capital_to_invest'
LEVERAGED_CAPITAL = 'leveraged_capital'
PROB_POSITIVE_HEADER = 'positive probability'
PROB_NEGATIVE_HEADER = 'negative probability'
COIN_SYMBOL = 'coin_symbol'
TIME_COLUMN_PREDICTION = 'prediction_time'
TIME_COLUMN_PRICE = 'ptime'
COINS_CANDLE_STICK_HEADERS = {'ptime', 'coin_symbol', '_close', '_high', '_low', '_open', '_volumeto'}

# ------------------ Updaters ------------------ #
REACH_TARGET_UPDATE = 'reach_target_update'
IS_EXPIRED = 'is_expired'
UPDATES_NEW_TIME_IS_LIQUIDATE = 'updates_new_time_is_liquidate'
IS_ACTIVE_INVEST_STRATEGY = 'is_active_invest_strategy'
FORCE_CLOSE_ALL_POSITIONS = 'force_close'

# ------------------ Running-Params ------------------ #
BENCHMARKS = [['BTC']]
TICK_TIME_HOURS = 1

# ------------------ PATHS ------------------ #
FEES_FILE_PATH = 'Fees/'
FEES_FILE_NAME = 'IndividualFees.csv'
ML_RESULT_LONG_PATH = 'MLResultsLongs/'
ML_RESULT_SHORT_PATH = 'MLResultsShorts/'
PATH_TO_WRITE_RESULT = "/opt/simulation"
PATH_TO_WRITE_PARTIAL_RESULT = "/tmp/"
os.makedirs(ML_RESULT_LONG_PATH, exist_ok=True)
os.makedirs(ML_RESULT_SHORT_PATH, exist_ok=True)


def set_path_to_write_result(result_path):
    global PATH_TO_WRITE_RESULT
    PATH_TO_WRITE_RESULT = os.path.join(result_path, 'simulation')