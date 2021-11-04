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

        for f in fundamental_scores[s]:
            for t in fundamentals_timeframes:
                current = json_data[0][f]
                historical = json_data[t][f]
                change = (current - historical)/historical * 100
                score = score_change([10, 20, 30, 50], change)

                fundamental_scores[s][f]['{} Q'.format(t)] = score

                # print('{} Period: {} Quarters\n{} -> {}\nChange: {:.2f}%    Score: {}\n'\
                #     .format(f, t, historical, current, change, score))

    print(json.dumps(fundamental_scores, indent=2))


if __name__ == '__main__':
    symbols = sys.argv[1:]
    main(symbols)
