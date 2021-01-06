import datetime
import json
import pandas as pd
import re
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

date_cols = ['date']
data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv", parse_dates=date_cols)
shares = {} # {PERMNO: {year: (start, end)}}


def consolidate_shares(data):
    # Get the code of all shares that are available at some point in time in the exchange and the corresponding
    # start and end index for each year
    global shares
    curr_share = data.iloc[0]['PERMNO']
    shares[curr_share] = {}
    prev_year = data.iloc[0]['date'].year
    start = 0

    for j, row in data.iterrows():
        print(j)

        curr_year = row['date'].year

        if pd.notna(row['PERMNO']) and row['PERMNO'] != curr_share:
            temp = shares[curr_share]
            temp[prev_year] = (start, j - 1)
            shares[curr_share] = temp

            prev_year = curr_year
            start = j
            curr_share = row['PERMNO']
            shares[curr_share] = {}

        elif curr_year != prev_year:
            temp = shares[curr_share]
            temp[prev_year] = (start, j - 1)
            shares[curr_share] = temp
            prev_year = curr_year
            start = j

    with open('result.json', 'w') as fp:
        json.dump(shares, fp)
    print(shares)


def find_shares(start_year):
    # Sieves out all stocks that have prices for all days within the formation period and the corresponding end siccode
    chosen_shares = []

    for permno, dates in shares.items():
        if start_year not in dates.keys() or start_year + 1 not in dates.keys or start_year + 2 not in dates.keys():
            continue

        is_complete = True
        for i in range(start_year, start_year + 3):
            start, end = dates[i]

            end_date = datetime.datetime(i, 12, 31)

            if end_date.weekday() == 6:                # Monday = 0, Sunday = 6
                end_date = end_date - datetime.timedelta(days=2)
            elif end_date.dt.dayofweek == 5:
                end_date = end_date - datetime.timedelta(days=1)

            end_date = pd.to_datetime(end_date)

            indicator = True
            for j in range(start, end + 1):
                if not bool(re.search('[1-9]+', str(data.iloc[j]['PRC']))) or not 100 <= data.iloc[j]['DLSTCD'] < 200:
                    '''
                    1. Discard the stock when it has missing price values
                    2. Discard the stock when it is delisted during the formation period
                    '''
                    indicator = False
                    break

                if j == end and not data.iloc[j]['date'] == end_date:
                    indicator = False

            if not indicator:
                is_complete = False
                break

        if is_complete:
            '''
            If the industry code of the PERMNO changes within the formation period, use the latest one to align with the 
            trading period
            '''
            chosen_shares.append([permno, data.iloc[dates[start_year+2][1]]['SICCD'], dates[start_year][0], dates[start_year+2][1]])

    '''
    start_date = pd.datetime.date(start_year, 1, 1)
    if start_date.dt.dayofweek == 7:
        start_date.apply(pd.DateOffset(1))
    elif start_date.dt.dayofweek == 6:
        start_date.apply(pd.DateOffset(2))

    end_date = pd.datetime.date(start_year + 2, 12, 31)

    if end_date.dt.dayofweek == 7:
        end_date.apply(pd.DateOffset(-2))
    elif end_date.dt.dayofweek == 6:
        end_date.apply(pd.DateOffset(-1))

    curr_date = start_date
    curr_share = shares[0]
    count = 1
    start_index = 0
    is_start = False

    for j, row in data.iterrows():
        if pd.notna(row['PERMNO']) and row['PERMNO'] == curr_share[0]:
            if row['date'] == curr_date and bool(re.search('[1-9]+', str(row['PRC']))):
                if is_start:
                    start_index = j

                if curr_date.dt.dayofweek == 5:
                    curr_date.apply(pd.DateOffset(3))
                else:
                    curr_date.apply(pd.DateOffset(1))

                if row['date'] == end_date and 100 <= row['DLSTCD'] < 200:
                    chosen_shares.append([curr_share[0], curr_share[1], start_index, j])

                    if count < len(shares):
                        curr_share = shares[count]
                        count += 1
                        curr_date = start_date
                        is_start = True
            else:
                if count < len(shares):
                    curr_share = shares[count]
                    count += 1
                    curr_date = start_date
                    is_start = True
    '''

    print(chosen_shares)
    return chosen_shares


if __name__ == '__main__':
    consolidate_shares(data)
    #relevant_shares = find_shares(2000)
    #relevant_shares = find_shares(2001)

    baseline_returns = []
    baseline_num_pairs_chosen = []
    baseline_num_pairs_traded = []

    '''
    for start_year in range(2000, 2017):
        relevant_shares = find_shares(start_year)

        # Baseline model
        baseline_pairs = baseline.main(data, relevant_shares)
        returns, num_pairs_traded = trade.trade(baseline_pairs, start_year + 3, data)
        baseline_returns.append(returns)
        baseline_num_pairs_traded.append(num_pairs_traded)
        baseline_num_pairs_chosen.append(len(baseline_pairs))

    analyse_returns.analyse_returns(baseline_returns, baseline_num_pairs_traded, baseline_num_pairs_chosen)
    '''