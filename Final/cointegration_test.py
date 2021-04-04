import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.tsa.stattools as st


def main(grouped_shares, p_value=0.05):

    ''' Identifies cointegrated pairs

    :param grouped_shares: List of shares to be considered separated by their individual groups
    :param p_value: Cointegration threshold
    :return: List of cointegrated pairs separated by their individual groups
    '''

    possible_pairs = form_pairs(grouped_shares)  # group: (share code, end row, log prices)
    cointegrated_pairs = find_cointegrated_pairs(possible_pairs, p_value)  # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta, sic_one, sic_two)]

    return cointegrated_pairs


def form_pairs(grouped_shares):

    ''' Generates all the possible pairs

    :param grouped_shares: List of shares to be considered separated by their individual groups
    :return: List of all possible pairs separated by their individual groups
    '''

    stationary_shares = {} # group: [(permno, dataframe, end_index, sic)]
    pairs = {}  # group: [(pair 1, pair 2)]

    for group, share_list in grouped_shares.items():
        stationary_shares[group] = []


        # Test for stationarity
        # ADF Test: Fail to reject null hypothesis --> Non-stationary (p-value > 0.05)
        for i in range(0, len(share_list)):
            adf_result = st.adfuller(share_list[i][2]['LOG_PRC'])

            if adf_result[1] > 0.05:
                temp = stationary_shares[group]
                temp.append((share_list[i][0], share_list[i][2], share_list[i][1], share_list[i][3]))
                stationary_shares[group] = temp

    for group, share_list in stationary_shares.items():
        pairs[group] = []

        for i in range(0, len(share_list)):
            for j in range(i + 1, len(share_list)):
                temp = pairs[group]
                temp.append((share_list[i], share_list[j]))
                pairs[group] = temp

    return pairs


def find_cointegrated_pairs(potential_pairs, p_value):

    ''' Tests pairs for cointegration

    :param potential_pairs: List of all possible pairs separated by their individual groups
    :param p_value: Cointegration threshold
    :return: List of cointegrated pairs separated by their individual groups
    '''

    selected_pairs = {}

    relevant_cols = ['date', 'PRC', 'LOG_PRC']

    for group, pairs in potential_pairs.items():
        selected_pairs[group] = []
        for i in range(0, len(pairs)):
            pair_one, pair_two = pairs[i]       # Share code, log_price series, end index, sic

            pair_one_prices = pair_one[1]
            pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

            pair_two_prices = pair_two[1]
            pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

            log_price_one = pair_one_price_series['LOG_PRC']
            log_price_two = pair_two_price_series['LOG_PRC']

            # Test for co-integration
            # Engle and Granger: Reject null hypothesis --> Co-integrated (p-value < 0.05)
            coint_t, pvalue, crit_value = st.coint(log_price_one, log_price_two)

            if pvalue < p_value:
                log_two_constant = sm.add_constant(log_price_two)
                model = sm.OLS(np.asarray(log_price_one), np.asarray(log_two_constant))
                results = model.fit()

                intercept, beta = results.params

                # Beta refers to how much of Stock 2 to buy to match the value of Stock A --> Cannot be -ve
                if beta > 0:
                    log_price_two = log_price_two.apply(lambda x:x*beta)
                    spread = log_price_one - log_price_two.values
                    mean = spread.mean()
                    std = spread.std()
                    speed_of_mean_reversion = approximate_speed(log_price_one.values, log_price_two.values)
                    pair = (pair_one[0], pair_one[2] + 1, pair_two[0], pair_two[2] + 1, mean, std, beta, pair_one[3], pair_two[3], speed_of_mean_reversion)
                    update_pair_list(group, pair, selected_pairs)
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
                        speed_of_mean_reversion = approximate_speed(log_price_two.values, log_price_one.values)
                        pair = (pair_two[0], pair_two[2] + 1, pair_one[0], pair_one[2] + 1, mean, std, beta, pair_one[3], pair_two[3], speed_of_mean_reversion)
                        update_pair_list(group, pair, selected_pairs)

    return selected_pairs


def update_pair_list(group, pair, selected_pairs):

    ''' Adds the newly identified pair to its group in the dictionary of selected_pairs

    :param group: Group of the pair
    :param pair: Newly identified pair to be added
    :param selected_pairs: Dictionary of selected pairs separated by groups
    :return: None
    '''

    temp = selected_pairs[group]
    temp.append(pair)
    selected_pairs[group] = temp


def approximate_speed(price_one, price_two):

    ''' Calculates the approximate speed of mean reversion of the pair

    :param price_one: Price series of stock one
    :param price_two: Price series of stock two
    :return: Approximate speed of mean reversion of the pair
    '''

    diff_one = []
    diff_two = []

    for index in range(1, len(price_one)):
        diff_one.append(price_one[index] - price_one[index-1])

    for index in range(1, len(price_two)):
        diff_two.append(price_two[index] - price_two[index-1])

    diff_two = sm.add_constant(diff_two)
    model = sm.OLS(diff_one, diff_two)
    results = model.fit()
    intercept, gamma = results.params

    return gamma
