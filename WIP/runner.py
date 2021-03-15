import json
import pandas as pd
import math
from WIP import baseline, trade, analyse_model, pre_process_data, dbscan, kmedoids, som, fuzzyk, analyse_clusters, generate_charts

# Data Files
date_cols = ['date']
#prices_data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_All.csv", parse_dates=date_cols)
prices_data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv", parse_dates=date_cols)
prices_data['PERMNO'] = prices_data['PERMNO'].astype(int)

shares = {} # {PERMNO: {year: (start, end)}}
trading_calendar = {2000: 252, 2001: 248, 2002: 252, 2003: 252, 2004: 252, 2005: 252, 2006: 251, 2007: 251, 2008: 253,
                   2009: 252, 2010: 252, 2011: 252, 2012: 250, 2013: 252, 2014: 252, 2015: 252, 2016: 252, 2017: 251,
                   2018: 251, 2019: 252}

date_cols = ['datadate']
#firm_data = pd.read_csv('/Users/elysiatan/PycharmProjects/thesis/Updated/Data_Firm_ALl.csv', parse_dates=date_cols)
firm_data = pd.read_csv('/Users/elysiatan/PycharmProjects/thesis/Updated/Data_Firm.csv', parse_dates=date_cols)
firm_data['LPERMNO'] = firm_data['LPERMNO'].astype(int)


def consolidate_shares(data):
    # Get the code of all shares that are available at some point in time in the exchange and the corresponding
    # start and end index for each year
    global shares

    try:
        with open('../Backup/result.json') as json_file:
       #with open('../Backup/result_All.json') as json_file:
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
    # Sieves out all stocks that have prices for all days within the formation period and the corresponding end siccode
    relevant_shares = []

    for permno, dates in shares.items():

        if str(start_year) not in dates.keys() or str(start_year + 1) not in dates.keys() or \
                str(start_year + 2) not in dates.keys() or str(start_year + 3) not in dates.keys():
            continue

        is_complete = True

        for i in range(start_year, start_year + 3):
            start, end = dates[str(i)]

            if (end - start) < (trading_calendar[i] - 1):
                # Missing prices in between
                is_complete = False
                break

            indicator = True
            for j in range(start, end + 1):
                '''
                if not bool(re.search('[1-9]+', str(prices_data.iloc[j]['PRC']))):
                    indicator = False
                    break
                '''
                if not prices_data.iloc[j]['PRC'] > 1.0 or not 100 <= prices_data.iloc[j]['DLSTCD'] < 200 or not int(prices_data.iloc[j]['VOL']) > 0:
                    #1. Discard the stock when it is delisted during the formation period
                    #2. Discard the stock when its price is less than $1 to avoid relatively high trading costs and
                    #complications (Faff et al, 2016)
                    #3. Discard the stock when its trading volume is 0 to replicate practical trading environments and
                    #deal with only liquid stocks (Faff et al, 2016)
                    indicator = False
                    break


            if not indicator:
                is_complete = False
                break

        if is_complete:
            '''
            If the industry code of the PERMNO changes within the formation period, use the latest one to align with the 
            trading period
            '''
            prices = prices_data.iloc[dates[str(start_year)][0]:dates[str(start_year + 2)][1] + 1]
            prices.loc[:, 'LOG_PRC'] = prices.apply(lambda row: math.log(row.PRC), axis=1)

            relevant_shares.append([permno, prices_data.iloc[dates[str(start_year + 2)][1]]['SICCD'], dates[str(start_year + 2)][1], prices])

    return relevant_shares


def standardise_share_list(relevant_shares, clustering_features):
    standardised_list = []
    index_mapping = {}

    for i in range(0, len(relevant_shares)):
        permno = relevant_shares[i][0]

        result = clustering_features.loc[clustering_features['permno'] == int(permno)]

        if len(result.values) != 0:
            index_mapping[permno] = len(standardised_list)
            standardised_list.append(relevant_shares[i])

    return standardised_list, index_mapping


def trader(pairs, start_year, prices_data, result_pairs_list, result_payoffs_per_pair_list, result_payoffs_per_day_list):
    num_pairs_traded, payoffs_per_pair, payoffs_per_day = trade.trade(pairs, start_year + 3, prices_data)

    result_pairs_list.append(pairs)
    result_payoffs_per_pair_list.append(payoffs_per_pair)
    result_payoffs_per_day_list.append(payoffs_per_day)


def save_results(pairs_list, payoffs_per_pair_list, payoffs_per_day_list, model):
    results = {}
    results["pairs_list"] = pairs_list
    results["payoffs_per_pair_list"] = payoffs_per_pair_list
    results["payoffs_per_day_list"] = payoffs_per_day_list

    file_name = "trading_results_" + model + ".json"
    with open(file_name, 'w') as fp:
        json.dump(results, fp)


if __name__ == '__main__':
    consolidate_shares(prices_data)

    baseline_pairs_list = []
    baseline_payoffs_per_pair_list = []
    baseline_payoffs_per_day_list = []

    dbscan_pairs_list = []
    dbscan_payoffs_per_pair_list = []
    dbscan_payoffs_per_day_list = []

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

        baseline_pairs = baseline.main(prices_data, standardised_share_list)
        trader(baseline_pairs, start_year, prices_data, baseline_pairs_list, baseline_payoffs_per_pair_list, baseline_payoffs_per_day_list)

        kmedoids_pairs = kmedoids.kmedoid_main(clustering_features, index_mapping, standardised_share_list)
        trader(kmedoids_pairs, start_year, prices_data, kmedoids_pairs_list, kmedoids_payoffs_per_pair_list, kmedoids_payoffs_per_day_list)

        fuzzyk_pairs = fuzzyk.fuzzy_main(clustering_features, index_mapping, standardised_share_list)
        trader(fuzzyk_pairs, start_year, prices_data, fuzzyk_pairs_list, fuzzyk_payoffs_per_pair_list, fuzzyk_payoffs_per_day_list)

        dbscan_pairs = dbscan.dbscan_main(clustering_features, index_mapping, standardised_share_list)
        trader(dbscan_pairs, start_year, prices_data, dbscan_pairs_list, dbscan_payoffs_per_pair_list, dbscan_payoffs_per_day_list)

    save_results(baseline_pairs_list, baseline_payoffs_per_pair_list, baseline_payoffs_per_day_list, "baseline")
    save_results(kmedoids_pairs_list, kmedoids_payoffs_per_pair_list, kmedoids_payoffs_per_day_list, "kmedoids")
    save_results(dbscan_pairs_list, dbscan_payoffs_per_pair_list, dbscan_payoffs_per_day_list, "dbscan")
    save_results(fuzzyk_pairs_list, fuzzyk_payoffs_per_pair_list, fuzzyk_payoffs_per_day_list, "fuzzy")
