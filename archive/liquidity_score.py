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
    score = 5
    for i, r in enumerate(ranges):
        if value - r < 0:
            score = i+1
            break
    return score


def main(symbols):
    api_config = load_api_cfg(API_CFG_PATH)

    alpaca_key = api_config['Alpaca']['key']
    alpaca_secret = api_config['Alpaca']['secret']

    alpaca_api = tradeapi.REST(alpaca_key, alpaca_secret)

    liquidity_timeframes = [1, 5, 20, 90]   # days
    absolute_vol_score_ranges = [1, 5, 10, 20]  # million
    relative_vol_score_ranges = [0.5, 0.6, 0.7, 0.8, 1.0]   # dimensionless
    average_vol_score_ranges = [1, 5, 10, 20]   # million

    liquidity_scores = {}

    bars_tables = alpaca_api.get_barset(symbols, '1D', limit=91).df
    for s in symbols:
        liquidity_scores[s] = {'Absolute vol.': {}, 'Relative vol.': {}, 'Average vol.': {}}

        symbol_table = bars_tables[s].sort_values(by=['time'], ascending=False)
        # print(symbol_table.head(6), '\n')

        five_day_average_vol = sum([v for v in symbol_table['volume'][0:5]])/5
        for t in liquidity_timeframes:
            absolute_vol = sum([v for v in symbol_table['volume'][0:t]])/1e6
            relative_vol = absolute_vol/(five_day_average_vol/1e6)
            average_vol = absolute_vol/t

            absolute_vol_score = score_change(absolute_vol_score_ranges, absolute_vol)
            relative_vol_score = score_change(relative_vol_score_ranges, relative_vol)
            average_vol_score = score_change(average_vol_score_ranges, average_vol)

            liquidity_scores[s]['Absolute vol.']['{} days'.format(t)] = absolute_vol_score
            liquidity_scores[s]['Relative vol.']['{} days'.format(t)] = relative_vol_score
            liquidity_scores[s]['Average vol.']['{} days'.format(t)] = average_vol_score

            # print('Period: {} days\nAbs.: {}    Score:{}\nRel.: {}    Score:{}\nAve.: {}    Score:{}\n'\
            #     .format(t, absolute_vol, absolute_vol_score, relative_vol, relative_vol_score, average_vol, average_vol_score))

    print(json.dumps(liquidity_scores, indent=2))



if __name__ == '__main__':
    symbols = sys.argv[1:]
    main(symbols)
