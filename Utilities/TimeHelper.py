import datetime
import time


def datetime_to_epoch(_datetime):
    return int((_datetime - datetime.datetime(1970, 1, 1)).total_seconds())


def epoch_to_date_time(epoch):
    return datetime.datetime.utcfromtimestamp(epoch)


def current_time_stamp():
    _now = datetime.datetime.utcnow()
    _timestamp = time.mktime(_now.timetuple())
    return _timestamp



if __name__ == '__main__':
    pass
    #print (epoch_to_date_time(1514768400))