# ELEC7080 group project

## Prerequisite

### FUTU Open API client (for getting market data)
<https://www.futunn.com/download/openAPI>

### TA-Lib x64/x86 (for building library)
<https://github.com/afnhsn/TA-Lib_x64>

### Anaconda
<https://www.anaconda.com/distribution/#download-section>

### Python library
    pip install futu-api
    pip install TA-Lib

## How to run
py getMarketData.py for getting market data
py main.py for main program
change strat_donchian_macd to strat_macd for comparision

## Strategy
1. Donchian channel + MACD
2. MACD only

## Assumptions
1. initial margin remains the same during the holding period
2. purchase price = average price of the day (high + low /2)