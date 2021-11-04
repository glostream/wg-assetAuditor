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

    financialmodelingprep_key = api_config['financialmodelingprep']['key']

    alpaca_api = tradeapi.REST(alpaca_key, alpaca_secret)

    liquidity_timeframes = [1, 5, 20, 90]   # days
    absolute_vol_score_ranges = [1, 5, 10, 20]  # million
    relative_vol_score_ranges = [0.5, 0.6, 0.7, 0.8, 1.0]   # dimensionless
    average_vol_score_ranges = [1, 5, 10, 20]   # million

    liquidity_scores = {'Absolute vol.': {}, 'Relative vol.': {}, 'Average vol.': {}}

    bars_tables = alpaca_api.get_barset(symbols, '1D', limit=91).df
    for s in symbols:
        symbol_table = bars_tables[s].sort_values(by=['time'], ascending=False)
        # symbol_table.at['2021-01-27', 'volume'] = 1
        print(symbol_table.head(6), '\n')
        five_day_average_vol = sum([v for v in symbol_table['volume'][0:5]])/5
        for t in liquidity_timeframes:
            absolute_vol = sum([v for v in symbol_table['volume'][0:t]])/1e6
            relative_vol = absolute_vol/(five_day_average_vol/1e6)
            average_vol = absolute_vol/t

            absolute_vol_score = score_change(absolute_vol_score_ranges, absolute_vol)
            relative_vol_score = score_change(relative_vol_score_ranges, relative_vol)
            average_vol_score = score_change(average_vol_score_ranges, average_vol)

            liquidity_scores['Absolute vol.']['{} days'.format(t)] = absolute_vol_score
            liquidity_scores['Relative vol.']['{} days'.format(t)] = relative_vol_score
            liquidity_scores['Average vol.']['{} days'.format(t)] = average_vol_score

            # print('Period: {} days\nAbs.: {}    Score:{}\nRel.: {}    Score:{}\nAve.: {}    Score:{}\n'\
            #     .format(t, absolute_vol, absolute_vol_score, relative_vol, relative_vol_score, average_vol, average_vol_score))

        price_timeframes = [1, 5, 20, 90]   # days
        price_score_ranges = [10, 20, 30, 50]   # percent

        price_scores = {'Price': {}}

        current_price = symbol_table['close'][0]
        for t in price_timeframes:
            historical_price = symbol_table['close'][t]

            price_change = (current_price - historical_price)/historical_price * 100
            price_change = price_change

            price_change_score = score_change(price_score_ranges, price_change)

            price_scores['Price']['{} days'.format(t)] = price_change_score

            # print('Period: {} days\n{} -> {}\nChange: {:.2f}%    Score: {}\n'\
            #     .format(t, historical_price, current_price, price_change, price_change_score))
        
        fundamentals_timeframes = [1, 2, 3, 4]  # financial quarters
        revenue_change_score_ranges = [10, 20, 30, 50]   # percent
        earnings_change_score_ranges = [10, 20, 30, 50]   # percent
        margin_change_score_ranges = [10, 20, 30, 50]   # percent

        fundamentals_url = 'https://financialmodelingprep.com/api/v3/income-statement/{}?period=quarter&limit=5&apikey={}'\
            .format(s, financialmodelingprep_key)
        r = requests.get(fundamentals_url)
        json_data = r.json()

        fundamental_scores = {'revenue': {}, 'netIncome': {}, 'grossProfitRatio': {}}

        for f in fundamental_scores:
            for t in fundamentals_timeframes:
                current = json_data[0][f]
                historical = json_data[t][f]
                change = (current - historical)/historical * 100
                score = score_change([10, 20, 30, 50], change)

                fundamental_scores[f]['{} Q'.format(t)] = score

                # print('{} Period: {} Quarters\n{} -> {}\nChange: {:.2f}%    Score: {}\n'\
                #     .format(f, t, historical, current, change, score))


        print(s, '\n')
        print(json.dumps(liquidity_scores, indent=2))
        print(json.dumps(price_scores, indent=2))
        print(json.dumps(fundamental_scores, indent=2))
        # print('\n\n')


if __name__ == '__main__':
    symbols = sys.argv[1:]
    main(symbols)
