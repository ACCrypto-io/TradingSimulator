# Trading Simulator/Backtesting
This project is to check your trading predictions and for checking diffrent strategies.
It was built for our CryptoCurrency ML predictions (but it can work with every asset), but the project is very easy to understand and well documented if you wish to make any changes.


### Installation
Developed and tested in Python 3.6 (please install python 3.6 and pip and python3.6 virtual environment).
Please install Numpy if you do not already have it (https://docs.scipy.org/doc/numpy/user/install.html).

Follow next steps to install project dependencies.
```sh
$ cd PROJECT_FOLDER_PATH
$ python3.6 -m venv env-simulator
$ source env-simulator/bin/activate
$ python3.6 -m pip install -r requirements.txt;
```

### Files for run
##### Coins price file
The file should be a compressed gzip csv file with the candlestick information,
it must contain the following headers:
 - ptime: the time of the candlestick (epoch timestamp in seconds).
 - coin_symbol: the coin symbol (e.x. BTC).
 - _close: the candlestick close price.
 - _high: the candlestick high price.
 - _low: the candle stick low price.
 - _open: the candlestick open price.
 - _volumeto: the candlestick volume to (e.x. for BTC coin_symbol is the number of US dollars traded for Bitcoins).

##### Prediction files
The predictions file should be located in 2 folders, MLResultsShorts and MLResultsLongs in the project directory (if not exist run the program once or just create the folders yourself). If you have predictions that are only for long positions insert them into the MLResultsLongs. For short positions put the predictions in the MLResultsShorts.
The predictions headers should be as follows:
 - prediction_time: time of prediction in the following format YYYY-MM-DDTHH (e.x. 2018-01-01T00).
 - coin_symbol: the asset/s that you wish to check the predictions for, the names must be capital letters (e.x. BTC).
 - high_boundary: the percentage to sell in case the asset reach this limit (e.x. if the simulation decided to buy this
 prediction, and the high_boundary is 0.1 and price at that time was 100, the simulation will sell if the price will reach 110).
 - low_boundary: the percentage to sell in case the asset reach this limit (e.x. if the simulation decided to buy this
 prediction, and the low_boundary is -0.01 and price at that time was 100, the simulation will sell if the price will reach 99).
 - time_predict: the prediction time in hours, this is the horizontal limit (e.x. if time_predict is 2 and in the 2 hours the price did not
 reach the high_boundary and not the low_boundary then it will sell 2 hours after the prediction time).
 - negative probability: the probability for the asset to reach the low_boundary, values need to be between 1.0 and 0.0 where 1.0 is the highest probability to reach the low_boundary and 0.0 is the lowest.
 - positive probability: the probability for the asset to reach the high_boundary, values need to be between 1.0 and 0.0 where 1.0 is the highest probability to reach the high_boundary and 0.0 is the lowest.


**Please note that the program does not check the files headers so it will throw an exception while running if any of the headers is not as described above.**

### General Simulation Information
- Tick interval: every tick the simulation simulate X hours has passed, it is currently adjusted for 1 hour tick. You find TICK_TIME_HOURS in the Utilities/Consts.py file to change the default configuration.
- Simulation Params: in the Utilities/SimulationParams.py file you can set all of the simulation possibilities you wish to run the backtesting. In the file there is a description for every parameter.
- Fees:
    - in the Fees/Fees.py file you can set the general simulation fees.
    - in the Fees/IndividualFees.csv file you can set individual fee for every asset.


### Run
If you did not follow the "Installation" or the "Files for run" sections, do not run the program.

When running the simulation, run with the following params:
-RunSimulations: boolean that indicates the app to start simulation.
-pathToCoinsPrice: the path to "Coins price file" from the "Files for run" section.
-benchmarkCoins: the benchmark you want your portfolio to compete against, the requested benchmark should be in the "Coins price file".
-resultPath: path of the simulator results.

Example
```sh
$ python3.6 Manager.py -RunSimulations -pathToCoinsPrice PRICE_CSV_PATH -benchmarkCoins BTC -resultPath /tmp/ > /tmp/simulation-run.log
```
The example will run the simulation and will write the results into /tmp/simulation folder. In the results the Alpha/Beta will be vs the BTC performance (Long on BTC).

For help and more descriptions run:
```sh
$ python3.6 Manager.py -h
```

### Result folder
In the result folder you will see folders numbered from 0 to number of different simulation permutations.
In every folder there are 3 files:
- capital_history.csv: full description of what was the capital in every tick (you can change tick time in the Utilities/Consts.py file).
- positions.csv: All positions in the simulation (Long/Short, time of holding the positions...)
- simulation.csv: the simulation params (one of the options set from Utilities/SimulationParams.py file).

### Notice
This project is a tool to help you check your financial ML model, but please note that this project does not know if your ML "cheated" (like one of the features is from the future...).
There are many places to make bad decisions. Before transferring all of your capital based on this simulation project please make a paper trading.

There are many places to improve in this project (e.x. some permutations have similar results like when setting the Shorts to be deactivate but changing only one parameter in the shorts params).

**DO NOT MAKE ANY DECISIONS THAT IS ONLY BASED ON THIS PROJECT!!!**