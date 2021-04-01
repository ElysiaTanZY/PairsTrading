import json
import math
import pandas as pd

from WIP import pre_process_data, baseline, dbscan, kmedoids, fuzzyk, trade

# Data Files
date_cols = ['date']
prices_data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv", parse_dates=date_cols)
prices_data['PERMNO'] = prices_data['PERMNO'].astype(int)

shares = {} # {PERMNO: {year: (start, end)}}
trading_calendar = {2000: 252, 2001: 248, 2002: 252, 2003: 252, 2004: 252, 2005: 252, 2006: 251, 2007: 251, 2008: 253,
                   2009: 252, 2010: 252, 2011: 252, 2012: 250, 2013: 252, 2014: 252, 2015: 252, 2016: 252, 2017: 251,
                   2018: 251, 2019: 252}

date_cols = ['datadate']
firm_data = pd.read_csv('/Users/elysiatan/PycharmProjects/thesis/Updated/Data_Firm.csv', parse_dates=date_cols)
firm_data['LPERMNO'] = firm_data['LPERMNO'].astype(int)


def consolidate_shares(data):

    ''' Map the PERMNO of each share that was available at some point in the exchange to its corresponding
    start and end index in the data set for each year

    :param data: All stocks in the data set
    :return: None
    '''

    global shares

    try:
        with open('../Backup/result.json') as json_file:
            shares = json.load(json_file)
            return
    except FileNotFoundError:
        pass

    curr_share = data.iloc[0]['PERMNO']
    shares[str(curr_share)] = {}
    prev_year = data.iloc[0]['date'].year
    start = 0

    for j, row in data.iterrows():
        curr_year = row['date'].year

        if pd.notna(row['PERMNO']) and row['PERMNO'] != curr_share:
            temp = shares[str(curr_share)]
            temp[str(prev_year)] = (start, j - 1)
            shares[str(curr_share)] = temp

            prev_year = curr_year
            start = j
            curr_share = row['PERMNO']
            shares[str(curr_share)] = {}

        elif curr_year != prev_year:
            temp = shares[str(curr_share)]
            temp[str(prev_year)] = (start, j - 1)
            shares[str(curr_share)] = temp
            prev_year = curr_year
            start = j

    with open('../Backup/result.json', 'w') as fp:
        json.dump(shares, fp)


def find_shares(start_year):

    ''' Sieves out stocks for the formation period of 3 years

    :param start_year: Starting year of the formation period
    :return: All stocks that meet the required criteria to be considered in the formation period and its corresponding end siccode
    '''

    relevant_shares = []

    for permno, dates in shares.items():

        if str(start_year) not in dates.keys() or str(start_year + 1) not in dates.keys() or \
                str(start_year + 2) not in dates.keys() or str(start_year + 3) not in dates.keys():
            continue

        is_complete = True

        for i in range(start_year, start_year + 3):
            start, end = dates[str(i)]

            # Missing prices in between
            if (end - start) < (trading_calendar[i] - 1):
                is_complete = False
                break

            indicator = True
            for j in range(start, end + 1):

                # 1. Discard the stock when it is delisted during the formation period
                # 2. Discard the stock when its price is less than $1 to avoid relatively high trading costs and
                # complications (Faff et al, 2016)
                # 3. Discard the stock when its trading volume is 0 to replicate practical trading environments and
                # deal with only liquid stocks (Faff et al, 2016)
                if not prices_data.iloc[j]['PRC'] > 1.0 or not 100 <= prices_data.iloc[j]['DLSTCD'] < 200 or not int(prices_data.iloc[j]['VOL']) > 0:
                    indicator = False
                    break

            if not indicator:
                is_complete = False
                break

        if is_complete:
            # If the SIC code of the PERMNO changes within the formation period, use the latest one to align with the
            # trading period
            prices = prices_data.iloc[dates[str(start_year)][0]:dates[str(start_year + 2)][1] + 1]
            prices.loc[:, 'LOG_PRC'] = prices.apply(lambda row: math.log(row.PRC), axis=1)

            relevant_shares.append([permno, prices_data.iloc[dates[str(start_year + 2)][1]]['SICCD'], dates[str(start_year + 2)][1], prices])

    return relevant_shares


def standardise_share_list(relevant_shares, clustering_features):

    ''' Gets the final list of shares to be considered during the formation period

    :param relevant_shares: List of shares that were qualified to be considered in the formation period
    :param clustering_features: List of qualified shares that have all the necessary input features
    :return: Intersection between relevant_shares and clustering_features
    '''

    standardised_list = []
    index_mapping = {}

    for i in range(0, len(relevant_shares)):
        permno = relevant_shares[i][0]

        result = clustering_features.loc[clustering_features['permno'] == int(permno)]

        if len(result.values) != 0:
            index_mapping[permno] = len(standardised_list)
            standardised_list.append(relevant_shares[i])

    return standardised_list, index_mapping


def trader(pairs_list, start_year, prices_data, result_pairs_list, result_payoffs_per_pair_list, result_payoffs_per_day_list):

    ''' Trades the pairs during the trading period

    :param pairs_list: Pairs that have been selected for trading
    :param start_year: Trading year
    :param prices_data: Price information of the shares to be traded
    :param result_pairs_list: List storing the list of pairs selected in each year
    :param result_payoffs_per_pair_list: List storing the list of payoffs made by selected pairs in each trading year
    :param result_payoffs_per_day_list: List storing the list of payoffs made each day in each trading year
    :return: None
    '''

    num_pairs_traded, payoffs_per_pair, payoffs_per_day = trade.trade(pairs_list, start_year + 3, prices_data)

    result_pairs_list.append(pairs_list)
    result_payoffs_per_pair_list.append(payoffs_per_pair)
    result_payoffs_per_day_list.append(payoffs_per_day)


def save_results(pairs_list, payoffs_per_pair_list, payoffs_per_day_list, model, num_outliers_list=None):

    ''' Saves the results obtained from backtesting

    :param pairs_list: List storing the list of pairs selected in each year
    :param payoffs_per_pair_list: List storing the list of payoffs made by selected pairs in each trading year
    :param payoffs_per_day_list: List storing the list of payoffs made each day in each trading year
    :param model: Model for which the results are attributed to
    :param num_outliers_list: List storing the number of outliers identified during clustering
    :return: None
    '''

    file_name = "trading_results_" + model + ".json"

    results = {}
    results["pairs_list"] = pairs_list
    results["payoffs_per_pair_list"] = payoffs_per_pair_list
    results["payoffs_per_day_list"] = payoffs_per_day_list

    # num_outliers_dict will only be present when DBSCAN is used for clustering
    if num_outliers_list != None:
        results["num_outliers_list"] = num_outliers_list

    with open(file_name, 'w') as fp:
        json.dump(results, fp)


def normal_runner():

    ''' Conducts the experiments to compare between Baseline and proposed Unsupervised Clustering methods

    :return: None
    '''

    consolidate_shares(prices_data)

    baseline_pairs_list = []
    baseline_payoffs_per_pair_list = []
    baseline_payoffs_per_day_list = []

    dbscan_pairs_list = []
    dbscan_payoffs_per_pair_list = []
    dbscan_payoffs_per_day_list = []
    num_outliers_list = []

    fuzzyk_pairs_list = []
    fuzzyk_payoffs_per_pair_list = []
    fuzzyk_payoffs_per_day_list = []

    kmedoids_pairs_list = []
    kmedoids_payoffs_per_pair_list = []
    kmedoids_payoffs_per_day_list = []

    for start_year in range(2000, 2017):
        print(start_year)
        relevant_shares = find_shares(start_year)
        clustering_features = pre_process_data.main(relevant_shares, firm_data, start_year)
        clustering_features['permno'] = clustering_features['permno'].astype(int)

        standardised_share_list, index_mapping = standardise_share_list(relevant_shares, clustering_features)

        # Baseline
        baseline_pairs = baseline.main(prices_data, standardised_share_list)
        trader(baseline_pairs, start_year, prices_data, baseline_pairs_list, baseline_payoffs_per_pair_list, baseline_payoffs_per_day_list)

        # K-Medoids
        kmedoids_pairs = kmedoids.kmedoid_main(clustering_features, index_mapping, standardised_share_list)
        trader(kmedoids_pairs, start_year, prices_data, kmedoids_pairs_list, kmedoids_payoffs_per_pair_list, kmedoids_payoffs_per_day_list)

        # Fuzzy C-Means
        fuzzyk_pairs = fuzzyk.fuzzy_main(clustering_features, index_mapping, standardised_share_list)
        trader(fuzzyk_pairs, start_year, prices_data, fuzzyk_pairs_list, fuzzyk_payoffs_per_pair_list, fuzzyk_payoffs_per_day_list)

        # DBSCAN
        dbscan_pairs, num_outliers = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list)
        num_outliers_list.append(num_outliers)
        trader(dbscan_pairs, start_year, prices_data, dbscan_pairs_list, dbscan_payoffs_per_pair_list, dbscan_payoffs_per_day_list)

    # Save results
    save_results(baseline_pairs_list, baseline_payoffs_per_pair_list, baseline_payoffs_per_day_list, "baseline")
    save_results(kmedoids_pairs_list, kmedoids_payoffs_per_pair_list, kmedoids_payoffs_per_day_list, "kmedoids")
    save_results(dbscan_pairs_list, dbscan_payoffs_per_pair_list, dbscan_payoffs_per_day_list, "dbscan", num_outliers_list)
    save_results(fuzzyk_pairs_list, fuzzyk_payoffs_per_pair_list, fuzzyk_payoffs_per_day_list, "fuzzy")


def feature_ablation_runner():

    ''' Conducts the Feature Ablation experiments

    :return: None
    '''

    consolidate_shares(prices_data)

    without_volume_pair_list = []
    without_volume_per_pair_list = []
    without_volume_per_day_list = []

    without_price_pair_list = []
    without_price_payoffs_per_pair_list = []
    without_price_payoffs_per_day_list = []
    without_price_outliers_list = []

    without_firm_fundamentals_pairs_list = []
    without_firm_fundamentals_payoffs_per_pair_list = []
    without_firm_fundamentals_payoffs_per_day_list = []
    without_firm_fundamentals_outliers_list = []

    for start_year in range(2000, 2017):
        print(start_year)
        relevant_shares = find_shares(start_year)

        # Volume of shares are not taken into account
        without_volume_relevant_shares_list = relevant_shares.copy()
        clustering_features = pre_process_data.main(without_volume_relevant_shares_list, firm_data, start_year, 1)
        clustering_features['permno'] = clustering_features['permno'].astype(int)

        standardised_share_list, index_mapping = standardise_share_list(without_volume_relevant_shares_list, clustering_features)

        without_volume_pairs, num_outliers = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list)
        trader(without_volume_pairs, start_year, prices_data, without_volume_pair_list, without_volume_per_pair_list,
               without_volume_per_day_list)

        # Price of shares are not taken into account
        without_price_relevant_shares_list = relevant_shares.copy()
        clustering_features = pre_process_data.main(without_price_relevant_shares_list, firm_data, start_year, 2)
        clustering_features['permno'] = clustering_features['permno'].astype(int)

        standardised_share_list, index_mapping = standardise_share_list(without_price_relevant_shares_list, clustering_features)

        without_price_pairs, num_outliers = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list)
        without_price_outliers_list.append(num_outliers)
        trader(without_price_pairs, start_year, prices_data, without_price_pair_list, without_price_payoffs_per_pair_list,
               without_price_payoffs_per_day_list)

        # Firm fundamentals of shares are not taken into account
        without_firm_fundamentals_relevant_shares_list = relevant_shares.copy()
        clustering_features = pre_process_data.main(without_firm_fundamentals_relevant_shares_list, firm_data, start_year, 3)
        clustering_features['permno'] = clustering_features['permno'].astype(int)

        standardised_share_list, index_mapping = standardise_share_list(without_firm_fundamentals_relevant_shares_list, clustering_features)

        without_firm_fundamentals_pairs, num_outliers = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list)
        without_firm_fundamentals_outliers_list.append(num_outliers)
        trader(without_firm_fundamentals_pairs, start_year, prices_data, without_firm_fundamentals_pairs_list, without_firm_fundamentals_payoffs_per_pair_list,
               without_firm_fundamentals_payoffs_per_day_list)

    # Save results
    save_results(without_volume_pair_list, without_volume_per_pair_list, without_volume_per_day_list, "without_volume")
    save_results(without_price_pair_list, without_price_payoffs_per_pair_list, without_price_payoffs_per_day_list, "without_price", without_price_outliers_list)
    save_results(without_firm_fundamentals_pairs_list, without_firm_fundamentals_payoffs_per_pair_list, without_firm_fundamentals_payoffs_per_day_list, "without_firm_fundamentals", without_firm_fundamentals_outliers_list)


def hyperparam_tuning_runner():

    ''' Conducts the experiments to analyse impact of varying portfolio size on portfolio performance

    :return: None
    '''

    consolidate_shares(prices_data)

    p_values = [0.01, 0.03, 0.075, 0.1]

    pair_list = {}
    payoffs_per_pair_list = {}
    payoffs_per_day_list = {}

    for p_value in p_values:
        pair_list[str(p_value)] = []
        payoffs_per_pair_list[str(p_value)] = []
        payoffs_per_day_list[str(p_value)] = []

    for start_year in range(2000, 2017):
        print(start_year)
        relevant_shares = find_shares(start_year)

        # Experiment was conducted without the volume feature because it was found to perform the best with DBSCAN
        clustering_features = pre_process_data.main(relevant_shares, firm_data, start_year, 1)
        clustering_features['permno'] = clustering_features['permno'].astype(int)

        standardised_share_list, index_mapping = standardise_share_list(relevant_shares, clustering_features)

        for p_value in p_values:
            pairs = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list, p_value)
            trader(pairs, start_year, prices_data, pair_list[str(p_value)], payoffs_per_pair_list[str(p_value)], payoffs_per_day_list[str(p_value)])

    # Save results
    for p_value in p_values:
        save_results(pair_list[str(p_value)], payoffs_per_pair_list[str(p_value)], payoffs_per_day_list[str(p_value)], str(p_value))


def pca_sensitivity_runner():

    ''' Conducts the experiments to analyse robustness against PCA components

    :return: None
    '''

    consolidate_shares(prices_data)

    pca_variation_list = [0.97, 0.99]

    pair_list = {}
    payoffs_per_pair_list = {}
    payoffs_per_day_list = {}
    outlier_list = {}

    for pca_variation in pca_variation_list:
        pair_list[str(pca_variation)] = []
        payoffs_per_pair_list[str(pca_variation)] = []
        payoffs_per_day_list[str(pca_variation)] = []
        outlier_list[str(pca_variation)] = []

    for start_year in range(2000, 2017):
        print(start_year)
        relevant_shares = find_shares(start_year)

        for pca_variation in pca_variation_list:
            # Experiment was conducted without the volume feature because it was found to perform the best with DBSCAN
            clustering_features = pre_process_data.main(relevant_shares, firm_data, start_year, 1, pca_variation)
            clustering_features['permno'] = clustering_features['permno'].astype(int)

            standardised_share_list, index_mapping = standardise_share_list(relevant_shares.copy(), clustering_features)
            pairs, num_outliers = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list)
            outlier_list[str(pca_variation)].append(num_outliers)
            trader(pairs, start_year, prices_data, pair_list[str(pca_variation)], payoffs_per_pair_list[str(pca_variation)], payoffs_per_day_list[str(pca_variation)])

    # Save results
    for pca_variation in pca_variation_list:
        save_results(pair_list[str(pca_variation)], payoffs_per_pair_list[str(pca_variation)], payoffs_per_day_list[str(pca_variation)], str(pca_variation), outlier_list[str(pca_variation)])


if __name__ == '__main__':
    # Tells the program which model should be run
    # 4 modes: normal, feature_ablation, hyperparam_tuning, pca
    model_to_be_run = 'pca'

    if model_to_be_run == 'normal':
        normal_runner()
    elif model_to_be_run == 'feature_ablation':
        feature_ablation_runner()
    elif model_to_be_run == 'hyperparam_tuning':
        hyperparam_tuning_runner()
    elif model_to_be_run == 'pca':
        pca_sensitivity_runner()
