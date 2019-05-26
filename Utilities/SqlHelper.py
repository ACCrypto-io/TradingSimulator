import datetime

import logging
import os

from Utilities import Consts

logger = logging.getLogger(__name__)

FOLDER_NAME = "SqlCommands/"
DB_NAME_HOLDER = '%replace_database_name%'

EXAMPLE = "Example.sql"

SELECT_COINS_FROM_COINS_DATA = "Coins_Data/selectCoinsFromCoinsData.sql"

_cached_query = {}
QUERY = "query"
MAX_CACHE_QUERYS = 20
LAST_USED = "last_used"


def __load_file(path):
    str_ret = ""
    try:
        with open(path, 'r') as f:
            for line in f.readlines():
                str_ret += line
    except Exception as e:
        logger.error("Tried to read a file but got exception, file name: {}, exception: {}".format(path, e))
        exit(0)
    return str_ret


def __pop_oldest_query():
    min_file = None
    min_date = datetime.datetime.utcnow()
    for file_name, dict_file in _cached_query.items():
        if dict_file[LAST_USED] < min_date:
            min_file = file_name
            min_date = dict_file[LAST_USED]
    if min_file in _cached_query:
        _cached_query.pop(min_file)


def load_sql_query(file_name, data_base_name=Consts.DB_NAME):
    if file_name in _cached_query:
        _cached_query[file_name][LAST_USED] = datetime.datetime.utcnow()
        return _cached_query[file_name][QUERY].replace(DB_NAME_HOLDER, data_base_name)
    if len(_cached_query) > MAX_CACHE_QUERYS:
        __pop_oldest_query()
    res = __load_file(FOLDER_NAME + file_name)
    if res != "":
        _cached_query[file_name] = {LAST_USED: datetime.datetime.utcnow(), QUERY: res}
    return res.replace(DB_NAME_HOLDER, data_base_name)

    # if __name__ == "__main__":
    #     print(load_sql_query(EXAMPLE))

