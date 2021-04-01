import json
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
from WIP import calculate_metrics_model, generate_charts, populate_result

ml_models = ["baseline", "dbscan", "fuzzy", "kmedoids"]
feature_ablation_models = ['without_volume', 'without_price', 'without_firm_fundamentals']
p_value_models = [0.01, 0.03, 0.075, 0.1]


def main(pair_list, returns, payoffs_per_day, model):
    return analyse_pairs(pair_list, returns, payoffs_per_day, model)   # returns: [[[(payoffs, start, end, start, end)]]]


def analyse_pairs(pair_lists, returns, payoffs_per_day, model):
    # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta, sic_one, sic_two)]
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        fama_groups = json.load(json_file)

    inter_industry_pairs = []  # List of all inter industry pairs across all years
    within_industry_pairs = []  # List of all within industry pairs across all years

    payoffs_inter_industry = []  # List of payoffs generated by inter industry pairs each year
    payoffs_within_industry = []  # List of payoffs generated by within industry pairs each year
    payoffs_combined = []
    # payoffs_series_inter_industry = []  # List of payoffs series generated by inter industry pairs each year
    # payoffs_series_within_industry = []  # List of payoffs series generated by within industry pairs each year

    traded_inter_industry = []  # List of traded inter industry pairs each year
    traded_within_industry = []  # List of traded within industry pairs each year
    traded_combined = []

    identified_inter_industry = []  # List of identified inter industry pairs each year
    identified_within_industry = []  # List of identified within industry pairs each year
    identified_combined = []

    inter_industry_pairs_dict = {}  # Splits the inter-indsutry pairs into their respective group pair
    beta_pairs_dict = {}  # Store the beta of chosen pairs
    payoffs_pairs_dict = {}  # Store the returns of chosen pairs separated by industry

    for year in range(0, len(pair_lists)):
        pair_list = pair_lists[year]
        returns_list = returns[year]

        inter_industry_payoffs_curr_year = 0
        within_industry_payoffs_curr_year = 0

        inter_industry_traded_curr_year = 0
        within_industry_traded_curr_year = 0

        inter_industry_identified_curr_year = 0
        within_industry_identified_curr_year = 0

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

                update_results(pair_one_group, pair_two_group, beta_pairs_dict, pair_list[group][pair][9])
                update_results(pair_one_group, pair_two_group, payoffs_pairs_dict, total_payoffs)

                # Inter-industry
                if pair_one_group != pair_two_group:
                    inter_industry_pairs.append(pair_list[group][pair])
                    inter_industry_identified_curr_year += 1

                    if total_payoffs != 0:
                        inter_industry_payoffs_curr_year += total_payoffs
                        inter_industry_traded_curr_year += 1

                    update_results(pair_one_group, pair_two_group, inter_industry_pairs_dict, total_payoffs)

                # Within industry
                else:
                    within_industry_pairs.append(pair_list[group][pair])
                    within_industry_identified_curr_year += 1

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

    labels = 'inter-industry', 'within-industry'
    sizes = [len(inter_industry_pairs), len(within_industry_pairs)]
    colors=["lightsteelblue", "steelblue"]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors)
    plt.axis('equal')
    plt.title('Pairs composition (' + model + ")")
    plt.show()

    print("\nPairs composition")
    headers = ["Industries", "Count", "Average Payoffs"]
    returns_list = [(k,) + v for k, v in payoffs_pairs_dict.items()]
    sorted_list = sorted(returns_list, key=lambda x: x[2], reverse=True)
    print(tabulate(sorted_list, headers=headers))

    print("\nInter-Industry Pairs Analysis:")
    calculate_metrics_model.analyse_returns(payoffs_inter_industry, traded_inter_industry, identified_inter_industry)

    print("\nWithin-Industry Pairs Analysis:")
    calculate_metrics_model.analyse_returns(payoffs_within_industry, traded_within_industry, identified_within_industry)

    print("\nAll:")
    fully_invested_return_list = calculate_metrics_model.analyse_returns(payoffs_combined, traded_combined, identified_combined)

    return fully_invested_return_list, identified_combined, traded_combined


def update_results(pair_one_group, pair_two_group, results_dict, new_value):

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


def generate_heat_map(results_dict, groups, title):
    groups_dict = {}   # Map the group to an index
    count = 0

    for group, value in groups.items():
        groups_dict[group] = count
        count += 1

    consolidated_result = []

    for i in range(0, count):
        group_result = []
        for j in range(0, count):
            group_result.append(0)
        consolidated_result.append(group_result)

    for pair, stats in results_dict.items():
        industry_one, industry_two = pair[0], pair[1]
        ave_beta = stats[1]

        index_one = groups_dict[industry_one]
        index_two = groups_dict[industry_two]

        consolidated_result[index_one][index_two] = ave_beta
        consolidated_result[index_two][index_one] = ave_beta

    plt.subplots(figsize=(30, 30))
    ax = sns.heatmap(consolidated_result, xticklabels=list(groups.keys()), yticklabels=list(groups.keys()))
    plt.title(title)
    plt.show()


if __name__ == '__main__':
    pairs_dict, payoffs_per_pair_dict, payoffs_per_day_dict = populate_result.main(ml_models)

    fully_invested_return_list = {}
    identified_pairs_list = {}
    traded_pairs_list = {}

    for model in ml_models:
        print(model)
        fully_invested_return_list[model], identified_pairs_list[model], traded_pairs_list[model] = main(pairs_dict[model], payoffs_per_pair_dict[model], payoffs_per_day_dict[model], model)
        print("\n")

    generate_charts.main(identified_pairs_list, traded_pairs_list, fully_invested_return_list, ml_models)