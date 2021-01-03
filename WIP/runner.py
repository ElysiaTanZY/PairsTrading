import pandas as pd

from WIP import baseline, trade, analyse_returns

# Data Files
'''
exchange_1 = pd.read_csv("../Updated/Exchange1update.csv")
exchange_1["date"] = exchange_1.Date.apply(lambda x: exchange_1.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

exchange_2 = pd.read_csv("../Updated/Exchange2update.csv")
exchange_2["date"] = exchange_2.Date.apply(lambda x: exchange_2.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

exchange_3 = pd.read_csv("../Updated/Exchange3update.csv")
exchange_3["date"] = exchange_3.Date.apply(lambda x: exchange_3.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date
'''

data = pd.read_csv("../Updated/Data-update.csv")


if __name__ == '__main__':
    baseline_returns = []
    baseline_num_pairs_chosen = []
    baseline_num_pairs_traded = []

    for start_year in range(2000, 2017):
        # Baseline model
        baseline_pairs = baseline.main(start_year, data)
        returns, num_pairs_traded = trade.trade(baseline_pairs, start_year + 3, data)
        baseline_returns.append(returns)
        baseline_num_pairs_traded.append(num_pairs_traded)
        baseline_num_pairs_chosen.append(len(baseline_pairs))

    analyse_returns.analyse_returns(baseline_returns, baseline_num_pairs_traded, baseline_num_pairs_chosen)