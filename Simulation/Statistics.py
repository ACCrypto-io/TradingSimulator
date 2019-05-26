
class Stats:
    def __init__(self, inital_capital):
        self.miss_positions = 0  # count all positions that missed target AKA hits the loss boundary
        self.hit_positions = 0  # count all positions hits target
        self.expired_positions_counter = 0  # count all positions that was expired
        self.stopped_positions_counter = 0  # count all positions that was stopped according to the active position strategy
        self.liquidated_positions = 0
        self.duplicate_shorts_and_longs_df = None  # df which describes the hours that a coin symbol had a long and short position simultaniously
        self.active_long_positions = []  # all active long positions
        self.active_short_positions = []  # all active shorts positions
        self.closed_long_positions = []  # all closed long positions
        self.closed_short_positions = []  # all closed shorts positions
        self.liquid_capital = inital_capital  # portfolio liquid_capital status
        self.hit_trail_positions = 0
        self.leverage_capital = 0.0
        self.long_capital = 0.0
        self.short_capital = 0.0
        self.fees_paid = 0.0 # Amount of fees paid

