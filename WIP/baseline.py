import json
import pandas as pd
import matplotlib as plt
import statsmodels.tsa.stattools as st


shares = []


def get_shares(data):
    # Get the code of all shares that are available in the exchanges
    global shares
    curr_share = data.iloc[0]['PERMNO']
    share_list = []

    for j, row in data.iterrows():
        if row['PERMNO'] != curr_share:
            share_list.append((curr_share, row['SICCD']))
            curr_share = row['PERMNO']

    shares.append(share_list)
    print(share_list)


def find_shares(_start_year_form, data):
    # Sieves out all stocks that have prices for all days within the formation period
    chosen_shares = []
    start_date = pd.datetime.date(_start_year_form, 1, 1)
    if start_date.dt.dayofweek == 7:
        start_date.apply(pd.DateOffset(1))
    elif start_date.dt.dayofweek == 6:
        start_date.apply(pd.DateOffset(2))

    end_date = pd.datetime.date(_start_year_form + 2, 12, 31)

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
        if row['PERMNO'] == curr_share[0]:
            if is_start:
                start_index = j

            if row['date'] == curr_date:
                if curr_date.dt.dayofweek == 5:
                    curr_date.apply(pd.DateOffset(3))
                else:
                    curr_date.apply(pd.DateOffset(1))

            elif row['date'] == end_date:
                chosen_shares.append([curr_share[0], curr_share[1], start_index, j])

                if count < len(shares):
                    curr_share = shares[count]
                    count += 1
                    curr_date = start_date
                    is_start = True
                else:
                    break

            else:
                if count < len(shares):
                    curr_share = shares[count]
                    count += 1
                    curr_date = start_date
                    is_start = True
                else:
                    break

        print(chosen_shares)

    return chosen_shares


def group_shares(relevant_shares):
    with open('../maskowitz_and_grinblatt.json') as json_file:
        data = json.load(json_file)

    groups = {}

    for i in range(0, len(relevant_shares)):
        sic_code = relevant_shares[i][1]

        if sic_code == 9999:
            name = 'unclassified'

            if name not in groups.keys():
                groups[name] = [(relevant_shares[i][0], relevant_shares[i][2], relevant_shares[i][3])]
            else:
                temp = groups[name]
                temp.append((relevant_shares[i][0], relevant_shares[i][2], relevant_shares[i][3]))
                groups[name] = temp

        for key, value in data.items():
            start = value['start']
            end = value['end']

            if start <= sic_code <= end:
                if key not in groups.keys():
                    groups[key] = [(relevant_shares[i][0], relevant_shares[i][2], relevant_shares[i][3])]
                else:
                    temp = groups[key]
                    temp.append((relevant_shares[i][0], relevant_shares[i][2], relevant_shares[i][3]))
                    groups[key] = temp

            break

    return groups


def form_pairs(grouped_shares):
    # Generate all the relevant pairs
    pairs = {}  # group: (pair 1, pair 2)

    for group, share_list in grouped_shares.items():
        pairs[group] = []

        for i in range(0, len(share_list)):
            for j in range(i, len(share_list)):
                temp = pairs[group]
                temp.append((share_list[i], share_list[j]))
                pairs[group] = temp

    return pairs


def cointegration(_ranked_pairs, data):
    # Test pairs for cointegration and return cointegrated pairs
    # Normalise price series before testing for cointegration
    # TODO: Heat map??? and stop once hit 20 actually check how many pairs are there in total and decide number from there
    selected_pairs = []

    relevant_cols = ['date', 'LOG_PRC']

    for key, pairs in _ranked_pairs.items():
        for i in range(0, len(pairs)):
            pair_one, pair_two = pairs[i]       # Share code, start row, end row

            pair_one_prices = data.iloc[pair_one[1]:pair_one[2] + 1]
            pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

            pair_two_prices = data.iloc[pair_two[1]:pair_two[2] + 1]
            pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

            # Plot time series
            ax = pair_one_price_series.plot(x='date', y='LOG_PRC')
            pair_two_price_series.plot(ax=ax)
            plt.show()

            # Test for co-integration
            coint_t, pvalue, crit_value = st.coint(pair_one_price_series['LOG_PRC'], pair_two_price_series['LOG_PRC'])

            if pvalue < 0.05:
                spread = pair_one_price_series['LOG_PRC'] - pair_two_price_series['LOG_PRC']
                mean = spread.mean()
                std = spread.std()
                pair = (pair_one[0], pair_one[2] + 1, pair_two[0], pair_two[2] + 1, mean, std)
                selected_pairs.append(pair)

    return selected_pairs

'''
#TODO: Not sure whether should rank beforehand and only pick the first few
def rank_pairs(_possible_pairs, data):
    # Rank the pairs based on sum of squared difference between normalised price series
    relevant_cols = ['date', 'LOG_PRC']
    for i in range(0, len(_possible_pairs)):
        pair_one, pair_two = _possible_pairs[i]

        pair_one_prices = data[pair_one[0]].iloc[pair_one[1]:pair_one[2] + 1]
        pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

        pair_two_prices = data[pair_two[0]].iloc[pair_two[1]:pair_two[2] + 1]
        pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

    return
'''

def main(start_year, data):
    # Formation period: 3 years + Trading period: 1 year (Rolling basis)
    # Start date: 1 Jan 2000
    get_shares(data)

    relevant_shares = find_shares(start_year, data)
    grouped_shares = group_shares(relevant_shares)
    possible_pairs = form_pairs(grouped_shares)         # group: (share code, start row, end row)
    #ranked_pairs = rank_pairs(possible_pairs, data)
    cointegrated_pairs = cointegration(possible_pairs, data)   # group: (pair_1, pair_2)
    return cointegrated_pairs
