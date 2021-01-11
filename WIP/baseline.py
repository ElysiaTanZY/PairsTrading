import json
import math
import matplotlib as plt
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as st
import statsmodels.api as sm


def group_shares(relevant_shares):
    # Adapted from: https: // github.com / alexchinco / CRSP - Data - Summary - Statistics - by - Industry - / blob / master / industries.json
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        data = json.load(json_file)

    groups = {}

    for i in range(0, len(relevant_shares)):
        print(i)
        sic_code = relevant_shares[i][1]
        if str(sic_code).isalpha():
            sic_code = int(9999)
        else:
            sic_code = int(sic_code)

        if sic_code == 9999:
            name = 'unclassified'
            update_groups(groups, name, relevant_shares, i)

        else:
            is_grouped = False
            for group, value in data.items():
                for sub_group, index in value.items():
                    start = int(index['start'])
                    end = int(index['end'])

                    if start <= sic_code <= end:
                        update_groups(groups, sub_group, relevant_shares, i)
                        is_grouped = True
                        break

                if is_grouped:
                    break

    with open('baseline_groups.json', 'w') as fp:
        json.dump(groups, fp)
    return groups


def update_groups(groups, name, relevant_shares, index):
    if name not in groups.keys():
        groups[name] = [(relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3])]
    else:
        temp = groups[name]
        temp.append((relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3]))
        groups[name] = temp


def form_pairs(grouped_shares, data):
    # Generate all the relevant pairs
    stationary_shares = {} # group: [(permno, log price, end_index)]
    pairs = {}  # group: [(pair 1, pair 2)]

    for group, share_list in grouped_shares.items():
        stationary_shares[group] = []

        '''
        Test for stationarity
        ADF Test: Fail to reject null hypothesis --> Non-stationary (p-value > 0.05)
        '''
        for i in range(0, len(share_list)):
            prices = data.iloc[share_list[i][1]:share_list[i][2] + 1]
            prices.loc[:, 'LOG_PRC'] = prices.apply(lambda row: math.log(row.PRC), axis=1)
            adf_result = st.adfuller(prices['LOG_PRC'])

            if adf_result[1] > 0.05:
                temp = stationary_shares[group]
                temp.append((share_list[i][0], prices, share_list[i][2]))
                stationary_shares[group] = temp

    for group, share_list in stationary_shares.items():
        pairs[group] = []

        # TODO: Rank the pairs based on sum of squared difference between log price series (Faff et al, 2016)
        for i in range(0, len(share_list)):
            for j in range(i + 1, len(share_list)):
                temp = pairs[group]
                temp.append((share_list[i], share_list[j]))
                pairs[group] = temp

    return pairs


def find_cointegrated_pairs(potential_pairs, data):
    # Test pairs for cointegration and return cointegrated pairs
    # Normalise price series before testing for cointegration
    # TODO: Heat map???
    selected_pairs = []

    relevant_cols = ['date', 'PRC', 'LOG_PRC']

    for key, pairs in potential_pairs.items():
        for i in range(0, len(pairs)):
            pair_one, pair_two = pairs[i]       # Share code, log_price series

            print(pair_one[0])
            print(pair_two[0])

            pair_one_prices = pair_one[1]
            pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

            pair_two_prices = pair_two[1]
            pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

            '''
            # Plot time series
            ax = pair_one_price_series.plot(x='date', y='LOG_PRC')
            pair_two_price_series.plot(ax=ax)
            plt.show()
            '''

            log_price_one = pair_one_price_series['LOG_PRC']
            log_price_two = pair_two_price_series['LOG_PRC']

            '''
            Test for co-integration
            Engle and Granger: Reject null hypothesis --> Co-integrated (p-value < 0.05)
            '''
            print(log_price_one.shape)
            print(log_price_two.shape)
            coint_t, pvalue, crit_value = st.coint(log_price_one, log_price_two)

            if pvalue < 0.05:
                print("Potential pair")
                log_two_constant = sm.add_constant(log_price_two)
                model = sm.OLS(np.asarray(log_price_one), np.asarray(log_two_constant))
                results = model.fit()

                intercept, beta = results.params

                if beta > 0:
                    log_price_two = log_price_two.apply(lambda x:x*beta)
                    spread = log_price_one - log_price_two.values
                    mean = spread.mean()
                    std = spread.std()
                    pair = (pair_one[0], pair_one[2] + 1, pair_two[0], pair_two[2] + 1, mean, std, beta)
                    selected_pairs.append(pair)
                else:
                    log_one_constant = sm.add_constant(log_price_one)
                    model = sm.OLS(np.asarray(log_price_two), np.asarray(log_one_constant))
                    results = model.fit()
                    intercept, beta = results.params

                    if beta > 0:
                        log_price_one = log_price_one.apply(lambda x: x * beta)
                        spread = log_price_two - log_price_one.values
                        mean = spread.mean()
                        std = spread.std()
                        pair = (pair_two[0], pair_two[2] + 1, pair_one[0], pair_one[2] + 1, mean, std, beta)
                        selected_pairs.append(pair)

    with open('selected_pairs.json', 'w') as fp:
        json.dump(selected_pairs, fp)

    return selected_pairs


def main(data, relevant_shares):
    # Formation period: 3 years + Trading period: 1 year (Rolling basis)
    print("Forming pairs")
    grouped_shares = group_shares(relevant_shares)
    possible_pairs = form_pairs(grouped_shares, data)         # group: (share code, start row, end row)
    cointegrated_pairs = find_cointegrated_pairs(possible_pairs, data)   # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta)]
    #return ranked_pairs
    return cointegrated_pairs


if __name__ == '__main__':
    with open('/Backup/chosen_shares_copy.json') as json_file:
        shares = json.load(json_file)

    date_cols = ['date']
    data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv", parse_dates=date_cols)

    grouped_shares = group_shares(shares)
    possible_pairs = form_pairs(grouped_shares, data)

    cointegrated_pairs = find_cointegrated_pairs(possible_pairs, data)

