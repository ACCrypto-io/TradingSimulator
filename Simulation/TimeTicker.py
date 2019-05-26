import logging
from Utilities import TimeHelper

logger = logging.getLogger("TimeTicker")


class TimeTicker:
    def __init__(self, initial_time, hours_tick_time_interval):
        self.current_time = initial_time  # Timestamp
        self.hours_tick_time_interval = hours_tick_time_interval  # Interval time in hours

    def advance_one_step(self):
        """
        Advances current time by ticktime interval
        :return:
        """
        self.current_time += (self.hours_tick_time_interval * 60 * 60)
        logger.debug("Simulation has advance to time {}".format(TimeHelper.epoch_to_date_time(self.current_time)))