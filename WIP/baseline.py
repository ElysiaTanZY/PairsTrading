import json
import math
import matplotlib as plt
import pandas as pd
import statsmodels.tsa.stattools as st
import statsmodels.api as sm


def group_shares(relevant_shares):
    with open('../maskowitz_and_grinblatt.json') as json_file:
        data = json.load(json_file)

    groups = {}

    for i in range(0, len(relevant_shares)):
        sic_code = relevant_shares[i][1]

        if sic_code == 9999:
            name = 'unclassified'
            update_groups(groups, name, relevant_shares, i)

        else:
            for key, value in data.items():
                start = value['start']
                end = value['end']

                if start <= sic_code <= end:
                    update_groups(groups, key, relevant_shares, i)
                break

    return groups


def update_groups(groups, name, relevant_shares, index):
    if name not in groups.keys():
        groups[name] = [(relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3])]
    else:
        temp = groups[name]
        temp.append((relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3]))
        groups[name] = temp


def form_pairs(grouped_shares):
    # Generate all the relevant pairs
    pairs = {}  # group: [(pair 1, pair 2)]

    for group, share_list in grouped_shares.items():
        pairs[group] = []

        for i in range(0, len(share_list)):
            for j in range(i, len(share_list)):
                temp = pairs[group]
                temp.append((share_list[i], share_list[j]))
                pairs[group] = temp

    return pairs


def find_cointegrated_pairs(potential_pairs, data):
    # Test pairs for cointegration and return cointegrated pairs
    # Normalise price series before testing for cointegration
    # TODO: Heat map???
    # TODO: Standardise price series
    selected_pairs = []

    relevant_cols = ['date', 'LOG_PRC']

    for key, pairs in potential_pairs.items():
        for i in range(0, len(pairs)):
            pair_one, pair_two = pairs[i]       # Share code, start row, end row

            pair_one_prices = data.iloc[pair_one[1]:pair_one[2] + 1]
            pair_one_prices['LOG_PRC'] = pair_one_prices.apply(lambda row: math.log(row['PRC'], 10), axis = 1)
            pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

            pair_two_prices = data.iloc[pair_two[1]:pair_two[2] + 1]
            pair_two_prices['LOG_PRC'] = pair_two_prices.apply(lambda row: math.log(row['PRC'], 10), axis=1)
            pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

            '''
            # Plot time series
            ax = pair_one_price_series.plot(x='date', y='LOG_PRC')
            pair_two_price_series.plot(ax=ax)
            plt.show()
            '''

            '''
            Test for stationarity
            ADF Test: Fail to reject null hypothesis --> Non-stationary (p-value > 0.05)
            '''
            adf_result_one = st.adfuller(pair_one_price_series)
            adf_result_two = st.adfuller(pair_two_price_series)

            if adf_result_one[1] <= 0.05 or adf_result_two <= 0.05:
                continue

            '''
            Test for co-integration
            Engle and Granger: Reject null hypothesis --> Co-integrated (p-value < 0.05)
            '''
            coint_t, pvalue, crit_value = st.coint(pair_one_price_series['LOG_PRC'], pair_two_price_series['LOG_PRC'])

            if pvalue < 0.05:
                pair_two_price_series = sm.add_constant(pair_two_price_series)
                model = sm.OLS(pair_one_price_series, pair_two_price_series)
                results = model.fit()
                intercept, beta = results.params

                if beta > 0:
                    pair_two_price_series['LOG_PRC'] = pair_two_price_series['LOG_PRC'].apply(lambda x:x*beta)
                    spread = pair_one_price_series['LOG_PRC'] - pair_two_price_series['LOG_PRC']
                    mean = spread.mean()
                    std = spread.std()
                    pair = (pair_one[0], pair_one[2] + 1, pair_two[0], pair_two[2] + 1, mean, std, beta)
                    selected_pairs.append(pair)
                else:
                    pair_one_price_series = sm.add_constant(pair_one_price_series)
                    model = sm.OLS(pair_two_price_series, pair_one_price_series)
                    results = model.fit()
                    intercept, beta = results.params

                    if beta > 0:
                        mean = spread.mean()
                        std = spread.std()
                        pair = (pair_two[0], pair_two[2] + 1, pair_one[0], pair_one[2] + 1, mean, std, beta)
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


def main(data, relevant_shares):
    # Formation period: 3 years + Trading period: 1 year (Rolling basis)
    grouped_shares = group_shares(relevant_shares)
    possible_pairs = form_pairs(grouped_shares)         # group: (share code, start row, end row)
    #ranked_pairs = rank_pairs(possible_pairs, data)

    cointegrated_pairs = find_cointegrated_pairs(possible_pairs, data)   # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta)]
    return cointegrated_pairs
