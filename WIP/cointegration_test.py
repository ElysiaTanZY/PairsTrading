import json
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as st
import statsmodels.api as sm


def main(grouped_shares, data):
    possible_pairs = form_pairs(grouped_shares, data)  # group: (share code, end row, log prices)
    cointegrated_pairs = find_cointegrated_pairs(possible_pairs)  # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta)]
    return cointegrated_pairs


def form_pairs(grouped_shares, data):
    # Generate all the relevant pairs
    stationary_shares = {} # group: [(permno, dataframe, end_index)]
    pairs = {}  # group: [(pair 1, pair 2)]

    for group, share_list in grouped_shares.items():
        stationary_shares[group] = []

        '''
        Test for stationarity
        ADF Test: Fail to reject null hypothesis --> Non-stationary (p-value > 0.05)
        '''
        for i in range(0, len(share_list)):
            adf_result = st.adfuller(share_list[i][2]['LOG_PRC'])

            if adf_result[1] > 0.05:
                temp = stationary_shares[group]
                temp.append((share_list[i][0], share_list[i][2], share_list[i][1]))
                stationary_shares[group] = temp

    for group, share_list in stationary_shares.items():
        pairs[group] = []

        # TODO: Rank the pairs based on sum of squared difference between log price series (Faff et al, 2016) - TBC
        for i in range(0, len(share_list)):
            for j in range(i + 1, len(share_list)):
                temp = pairs[group]
                temp.append((share_list[i], share_list[j]))
                pairs[group] = temp

    return pairs


def find_cointegrated_pairs(potential_pairs):
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