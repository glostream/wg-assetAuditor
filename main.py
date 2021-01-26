import alpaca_trade_api as tradeapi
import json
import sys
import pandas as pd
import requests


CFG_PATH = 'api.json'


def load_api_cfg(path):
    with open(path, 'r') as f:
        config = json.load(f)
        return config


def score(ranges, value):
    score = 5
    for i, r in enumerate(ranges):
        if value - r < 0:
            score = i+1
            break
    return score


def main(symbols):
    api_config = load_api_cfg(CFG_PATH)

    alpaca_key = api_config['Alpaca']['key']
    alpaca_secret = api_config['Alpaca']['secret']

    financialmodelingprep_key = api_config['financialmodelingprep']['key']

    alpaca_api = tradeapi.REST(alpaca_key, alpaca_secret)

    liquidity_timeframes = [1, 5, 20, 90]   # days
    absolute_vol_score_ranges = [1, 5, 10, 20]  # million
    relative_vol_score_ranges = [0.5, 0.6, 0.7, 0.8, 1.0]   # dimensionless
    average_vol_score_ranges = [1, 5, 10, 20]   # million

    bars_tables = alpaca_api.get_barset(symbols, '1D', limit=91).df
    for s in symbols:
        symbol_table = bars_tables[s].sort_values(by=['time'], ascending=False)
        # print(symbol_table)
        five_day_average_vol = sum([v for v in symbol_table['volume'][1:5+1]])/5
        for t in liquidity_timeframes:
            absolute_vol = sum([v for v in symbol_table['volume'][1:t+1]])/1e6
            relative_vol = absolute_vol/(five_day_average_vol/1e6)
            average_vol = absolute_vol/t

            absolute_vol_score = score(absolute_vol_score_ranges, absolute_vol)
            relative_vol_score = score(relative_vol_score_ranges, relative_vol)
            average_vol_score = score(average_vol_score_ranges, average_vol)

            # print('Period: {} days\nAbs: {}    Score:{}\nRel: {}    Score:{}\nAve: {}    Score:{}\n'\
            #     .format(t, absolute_vol, absolute_vol_score, relative_vol, relative_vol_score, average_vol, average_vol_score))

        price_timeframes = [1, 5, 20, 90]   # days
        price_score_ranges = [10, 20, 30, 50]   # percent

        current_price = symbol_table['close'][0]
        for t in price_timeframes:
            historical_price = symbol_table['close'][t]

            price_change = (current_price - historical_price)/historical_price * 100
            price_change = abs(price_change)

            price_change_score = score(price_score_ranges, price_change)

            # print('Period: {} days\n{} - {}\nChange: {}    Score: {}\n'\
            #     .format(t, current_price, historical_price, price_change, price_change_score))
        

        fundamentals_timeframes = [1, 2, 3, 4]  # financial quarters
        revenue_change_score_ranges = [10, 20, 30, 50]   # percent
        earnings_change_score_ranges = [10, 20, 30, 50]   # percent
        margin_change_score_ranges = [10, 20, 30, 50]   # percent

        fundamentals_url = 'https://financialmodelingprep.com/api/v3/income-statement/{}?period=quarter&limit=4&apikey={}'\
            .format(s, financialmodelingprep_key)
        r = requests.get(fundamentals_url)
        json_data = json.loads(r.text)

        current_revenue = json_data[0]['revenue']
        current_earnings = json_data[0]['netIncome']
        current_margin = json_data[0]['grossProfitRatio']
        for t in fundamentals_timeframes:
            historical_revenue = json_data[t]['revenue']
            historical_earnings = json_data[t]['netIncome']
            historical_margin = json_data[t]['grossProfitRatio']

            revenue_change = (current_revenue - historical_revenue)/historical_revenue * 100
            earnings_change = (current_earnings - historical_earnings)/historical_earnings * 100
            margin_change = (current_margin - historical_margin)/historical_margin * 100

            revenue_change = abs(revenue_change)
            earnings_change = abs(earnings_change)
            margin_change = abs(margin_change)

            revenue_change_score = score(revenue_change_score_ranges, revenue_change)
            earnings_change_score = score(earnings_change_score_ranges, earnings_change)
            margin_change_score = score(margin_change_score_ranges, margin_change)

            
            print('Period: {} quarters\n{} - {}\nChange: {}    Score: {}\n'\
                .format(t, current_revenue, historical_revenue, revenue_change, revenue_change_score))


if __name__ == '__main__':
    symbols = sys.argv[1:]
    main(symbols)
