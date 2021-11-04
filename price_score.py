import alpaca_trade_api as tradeapi
import json
import sys
import pandas as pd
import requests


API_CFG_PATH = 'api.json'


def load_api_cfg(path):
    with open(path, 'r') as f:
        config = json.load(f)
        return config


def score_change(ranges, value):
    # print(value, ranges)
    if value > ranges[-1]: return 5
    if value < ranges[0]: return 1
    for i, r in enumerate(ranges):
        if value - r < 0:
            lower_bound = ranges[i-1]
            upper_bound = r
            # print(lower_bound, upper_bound)
            score = (value - lower_bound) / (upper_bound - lower_bound) + i+1
            return round(score, 2)


def main(symbols):
    api_config = load_api_cfg(API_CFG_PATH)

    alpaca_key = api_config['Alpaca']['key']
    alpaca_secret = api_config['Alpaca']['secret']

    alpaca_api = tradeapi.REST(alpaca_key, alpaca_secret)

    price_timeframes = [1, 5, 20, 90]   # days
    price_score_ranges = [10, 20, 30, 50]   # percent
    price_scores = {}

    bars_tables = alpaca_api.get_barset(symbols, '1D', limit=91).df
    for s in symbols:
        symbol_table = bars_tables[s].sort_values(by=['time'], ascending=False)
        # print(symbol_table.head(6), '\n')

        price_scores[s] = {'Price': {}}

        current_price = symbol_table['close'][0]
        for t in price_timeframes:
            historical_price = symbol_table['close'][t]

            price_change = (current_price - historical_price)/historical_price * 100
            price_change = price_change

            price_change_score = score_change(price_score_ranges, price_change)

            price_scores[s]['Price']['{} days'.format(t)] = {'value': '{}%'.format(round(price_change, 2)), 'score': price_change_score}

            # print('Period: {} days\n{} -> {}\nChange: {:.2f}%    Score: {}\n'\
            #     .format(t, historical_price, current_price, price_change, price_change_score))
        
    print(json.dumps(price_scores, indent=2))


if __name__ == '__main__':
    symbols = sys.argv[1:]
    symbols = [s.upper() for s in symbols]
    main(symbols)
