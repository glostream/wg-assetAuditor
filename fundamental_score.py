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

    financialmodelingprep_key = api_config['financialmodelingprep']['key']

    fundamentals_timeframes = [1, 2, 3, 4]  # financial quarters
    revenue_change_score_ranges = [10, 20, 30, 50]   # percent
    earnings_change_score_ranges = [10, 20, 30, 50]   # percent
    margin_change_score_ranges = [10, 20, 30, 50]   # percent

    fundamental_scores = {}

    for s in symbols:
        fundamental_scores[s] = {'revenue': {}, 'netIncome': {}, 'grossProfitRatio': {}}

        fundamentals_url = 'https://financialmodelingprep.com/api/v3/income-statement/{}?period=quarter&limit=5&apikey={}'\
            .format(s, financialmodelingprep_key)
        r = requests.get(fundamentals_url)
        json_data = r.json()

        # for e in json_data:
        #     print(e['date'], e['period'])
        # print(json_data)

        for f in fundamental_scores[s]:
            for t in fundamentals_timeframes:
                # current = json_data[0][f]
                current = json_data[t-1][f]
                historical = json_data[t][f]
                change = (current - historical)/historical * 100
                score = score_change([10, 20, 30, 50], change)

                fundamental_scores[s][f]['{} Q'.format(t)] = {'value': '{}%'.format(round(change, 2)), 'score': score}

                # print('{} Period: {} Quarters\n{} -> {}\nChange: {:.2f}%    Score: {}\n'\
                #     .format(f, t, historical, current, change, score))

    print(json.dumps(fundamental_scores, indent=2))


if __name__ == '__main__':
    symbols = sys.argv[1:]
    symbols = [s.upper() for s in symbols]
    main(symbols)
