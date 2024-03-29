import json
import matplotlib.pyplot as plt
import statistics
from tabulate import tabulate

from Final import calculate_metrics, generate_charts, populate_result

# Compare ML clustering with baseline cluster by industry groups (baseline_model: baseline)
ml_models = ["baseline", "dbscan", "fuzzy", "kmedoids"]

# Compare the performance of the model when different feature sets are used (baseline_model = all)
feature_ablation_models = ['without_volume', 'without_price', 'without_firm_fundamentals', 'dbscan']

# Compare the performance of the model when different p_values are used when testing for cointegration (baseline_model = 0.05)
p_value_models = [0.01, 0.03, 0.075, 0.1]

# Compare the performance of the model when different pca_variation are used (baseline_model = 0.95)
pca_models = [0.97, 0.99]

# Indicator of the models to be compared (To be changed accordingly)
model_list = feature_ablation_models


def main(pair_list, payoffs_per_pair_list, model):

    ''' Calculates the necessary financial metrics for the given model

    :param pair_list: List of pairs identified by the model in each year
    :param payoffs_per_pair_list: List of payoffs made by each identified pair (separate list for each year)
    :param model: Model in concern
    :return: List of return on committed capital per year, number of identied pairs per year,
    number of traded pairs per year
    '''

    return analyse_pairs(pair_list, payoffs_per_pair_list, model)


def analyse_pairs(pair_lists, payoffs_per_pair_list, model):

    ''' Analyses the pairs generated by the model

    :param pair_lists: List of pairs identified by the model in each year
    :param payoffs_per_pair_list: List of payoffs made by each identified pair (separate list for each year)
    :param model: Model in concern
    :return: List of return on committed capital per year, number of identied pairs per year,
    number of traded pairs per year
    '''

    # payoffs_per_pair_list: [{group:[(payoffs, start, end, start, end)]}]
    # pair_lists: [{group: [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta, sic_one, sic_two)]}]
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        fama_groups = json.load(json_file)

    inter_industry_pairs = []           # List of inter-industry pairs formed per year
    within_industry_pairs = []          # List of within industry pairs formed per year

    payoffs_inter_industry = []         # Total payoffs generated by inter-industry pairs per year
    payoffs_within_industry = []        # Total payoffs generated by within-industry pairs per year
    payoffs_combined = []               # Total payoffs generated by all pairs per year

    traded_inter_industry = []          # Number of traded inter-industry pairs per year
    traded_within_industry = []         # Number of traded within-industry pairs per year
    traded_combined = []

    identified_inter_industry = []      # Number of identified inter-industry pairs per year
    identified_within_industry = []     # Number of identified within-industry pairs per year
    identified_combined = []

    num_trades_inter_industry = []      # Number of trades involving inter-industry pairs per year
    num_trades_within_industry = []     # Number of trades involving within-industry pairs per year
    num_trades_combined = []            # Total number of trades per year

    inter_industry_pairs_dict = {}      # Splits the inter-indsutry pairs into their respective group pair
    beta_pairs_dict = {}                # Store the beta of chosen pairs separated by (industry1, industry2)
    payoffs_pairs_dict = {}             # Store the returns of chosen pairs separated by (industry1, industry2)
    beta_list = []                      # Store the beta of chosen pairs regardless of industry

    for year in range(0, len(pair_lists)):
        pair_list = pair_lists[year]
        returns_list = payoffs_per_pair_list[year]

        inter_industry_payoffs_curr_year = 0
        within_industry_payoffs_curr_year = 0

        inter_industry_traded_curr_year = 0
        within_industry_traded_curr_year = 0

        inter_industry_identified_curr_year = 0
        within_industry_identified_curr_year = 0

        inter_industry_num_trades_curr_year = 0
        within_industry_num_trades_curr_year = 0

        for group in pair_list.keys():
            # Check number of pairs in pair_list and returns_list is the same
            if len(pair_list[group]) != len(returns_list[group]):
                raise Exception("Something wrong when storing pairs and returns in trading script")

            for pair in range(0, len(pair_list[group])):
                sic_one = int(pair_list[group][pair][7])
                sic_two = int(pair_list[group][pair][8])

                is_identified_group_one = False
                is_identified_group_two = False

                for fama_group, value in fama_groups.items():
                    for sub_group, index in value.items():
                        start = int(index['start'])
                        end = int(index['end'])

                        if start <= sic_one <= end:
                            pair_one_group = fama_group
                            is_identified_group_one = True

                        if start <= sic_two <= end:
                            pair_two_group = fama_group
                            is_identified_group_two = True

                        if is_identified_group_one and is_identified_group_two:
                            break

                    if is_identified_group_one and is_identified_group_two:
                        break

                total_payoffs = sum(x[0] for x in returns_list[group][pair])

                beta_list.append(pair_list[group][pair][9])
                update_results(pair_one_group, pair_two_group, beta_pairs_dict, pair_list[group][pair][9])
                update_results(pair_one_group, pair_two_group, payoffs_pairs_dict, total_payoffs)

                # Inter-industry
                if pair_one_group != pair_two_group:
                    inter_industry_pairs.append(pair_list[group][pair])
                    inter_industry_identified_curr_year += 1
                    inter_industry_num_trades_curr_year += len(returns_list[group][pair])

                    if total_payoffs != 0:
                        inter_industry_payoffs_curr_year += total_payoffs
                        inter_industry_traded_curr_year += 1

                    update_results(pair_one_group, pair_two_group, inter_industry_pairs_dict, total_payoffs)

                # Within industry
                else:
                    within_industry_pairs.append(pair_list[group][pair])
                    within_industry_identified_curr_year += 1
                    within_industry_num_trades_curr_year += len(returns_list[group][pair])

                    if total_payoffs != 0:
                        within_industry_payoffs_curr_year += total_payoffs
                        within_industry_traded_curr_year += 1

        payoffs_inter_industry.append(inter_industry_payoffs_curr_year)
        payoffs_within_industry.append(within_industry_payoffs_curr_year)
        payoffs_combined.append(inter_industry_payoffs_curr_year + within_industry_payoffs_curr_year)

        traded_inter_industry.append(inter_industry_traded_curr_year)
        traded_within_industry.append(within_industry_traded_curr_year)
        traded_combined.append(inter_industry_traded_curr_year + within_industry_traded_curr_year)

        identified_inter_industry.append(inter_industry_identified_curr_year)
        identified_within_industry.append(within_industry_identified_curr_year)
        identified_combined.append(inter_industry_identified_curr_year + within_industry_identified_curr_year)

        num_trades_inter_industry.append(inter_industry_num_trades_curr_year)
        num_trades_within_industry.append(within_industry_num_trades_curr_year)
        num_trades_combined.append(inter_industry_num_trades_curr_year + within_industry_num_trades_curr_year)

    # Plots the number of inter and intra-industry pairs as a proportion of total number of pairs
    labels = 'inter-industry', 'within-industry'
    sizes = [len(inter_industry_pairs), len(within_industry_pairs)]
    colors=["lightsteelblue", "steelblue"]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors)
    plt.axis('equal')
    plt.title('Pairs composition (' + model + ")")
    plt.show()

    # Prints the average payoffs of an (industry, industry) pair ranked in descending order
    print("\nPayoff rankings")
    headers = ["Industries", "Count", "Average Payoffs"]
    returns_list = [(k,) + v for k, v in payoffs_pairs_dict.items()]
    sorted_list = sorted(returns_list, key=lambda x: x[2], reverse=True)
    print(tabulate(sorted_list, headers=headers))

    # Prints financial metrics of inter-industry pairs
    print("\nInter-Industry Pairs Analysis:")
    calculate_metrics.analyse_returns(payoffs_inter_industry, traded_inter_industry, identified_inter_industry, num_trades_inter_industry)

    # Prints financial metrics of intra-industry pairs
    print("\nWithin-Industry Pairs Analysis:")
    calculate_metrics.analyse_returns(payoffs_within_industry, traded_within_industry, identified_within_industry, num_trades_within_industry)

    # Prints financial metrics of all pairs
    print("\nAll:")
    return_on_committed_capital_list = calculate_metrics.analyse_returns(payoffs_combined, traded_combined, identified_combined, num_trades_combined)

    print("\nAverage Beta:")
    print(statistics.mean(beta_list))

    return return_on_committed_capital_list, identified_combined, traded_combined


def update_results(pair_one_group, pair_two_group, results_dict, new_value):

    ''' Updates the results_dict with new information

    :param pair_one_group: Group of the first stock in the pair
    :param pair_two_group: Group of the second stock in the pair
    :param results_dict: Dictionary to be updated (beta_pairs_dict, inter_industry_pairs_dict, payoffs_pairs_dict)
    :param new_value: new_value to be added to the value of the corresponding key in the results_dict
    :return: None
    '''

    if (pair_one_group, pair_two_group) in results_dict.keys():
        prev_count, prev_average = results_dict[(pair_one_group, pair_two_group)]
        new_count = prev_count + 1
        new_average = (prev_average * prev_count + new_value) / new_count
        results_dict[(pair_one_group, pair_two_group)] = (new_count, new_average)
    elif (pair_two_group, pair_one_group) in results_dict.keys():
        prev_count, prev_average = results_dict[(pair_two_group, pair_one_group)]
        new_count = prev_count + 1
        new_average = (prev_average * prev_count + new_value) / new_count
        results_dict[(pair_two_group, pair_one_group)] = (new_count, new_average)
    else:
        results_dict[(pair_one_group, pair_two_group)] = (1, new_value)


if __name__ == '__main__':
    pairs_dict, payoffs_per_pair_dict, payoffs_per_day_dict, num_outliers_dict = populate_result.main(model_list)

    return_on_committed_capital_list = {}
    identified_pairs_list = {}
    traded_pairs_list = {}

    for model in model_list:
        print(model)
        model = str(model)
        return_on_committed_capital_list[model], identified_pairs_list[model], traded_pairs_list[model] = main(pairs_dict[model], payoffs_per_pair_dict[model], model)
        print("\n")

    print(num_outliers_dict.items())
    generate_charts.main(identified_pairs_list, traded_pairs_list, return_on_committed_capital_list, model_list)