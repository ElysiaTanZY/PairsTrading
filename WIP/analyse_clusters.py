import json
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import statistics
from tabulate import tabulate

from WIP import populate_result

models = ["baseline", "dbscan"]

def main(pair_list, returns, payoffs_per_day=None):
    analyse_pairs(pair_list, returns, payoffs_per_day)   # returns: [[[(payoffs, start, end, start, end)]]]


def analyse_pairs(pair_lists, returns, payoffs_per_day):
    # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta, sic_one, sic_two)]
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        groups = json.load(json_file)

    return_on_committed_capital_dict = {}
    fully_invested_return_dict = {}
    for year in range(15, 17):
    #for year in range(0, len(pair_lists)):
        pair_list = pair_lists[year]
        payoffs_list = returns[year]
        #print(year)

        returns_list = []

        for group in pair_list.keys():
            if group not in return_on_committed_capital_dict.keys():
                return_on_committed_capital_dict[group] = []

            if group not in fully_invested_return_dict.keys():
                fully_invested_return_dict[group] = []

            inter_industry_pairs = []        # List of all inter industry pairs in the cluster
            within_industry_pairs = []       # List of all within industry pairs in the cluster

            inter_industry_pairs_dict = {}   # Splits the inter-indsutry pairs into their respective group pair
            pairs_beta_dict = {}                  # Store the groups of chosen pairs
            pairs_payoffs_dict = {}                # Store the returns of chosen pairs separated by industry

            if len(pair_list[group]) != len(payoffs_list[group]):
                raise Exception("Something wrong when storing pairs and returns in trading script")

            inter_industry_payoffs_curr_group = 0
            within_industry_payoffs_curr_group = 0

            inter_industry_traded_curr_group = 0
            within_industry_traded_curr_group = 0

            inter_industry_identified_curr_group = 0
            within_industry_identified_curr_group = 0

            for pair in range(0, len(pair_list[group])):
                sic_one = int(pair_list[group][pair][7])
                sic_two = int(pair_list[group][pair][8])

                is_identified_group_one = False
                is_identified_group_two = False

                for fama_group, value in groups.items():
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

                total_payoffs = sum(x[0] for x in payoffs_list[group][pair])

                # Update Beta Map
                update_results(pair_one_group, pair_two_group, pairs_beta_dict, pair_list[group][pair][9], True)

                # Update Payoffs Map
                update_results(pair_one_group, pair_two_group, pairs_payoffs_dict, total_payoffs)

                # Inter-industry
                if pair_one_group != pair_two_group:
                    #inter_industry_payoffs_series_curr.extend(returns[j][i])
                    inter_industry_pairs.append(pair_list[group][pair])
                    inter_industry_identified_curr_group += 1

                    if total_payoffs != 0:
                        inter_industry_payoffs_curr_group += total_payoffs
                        inter_industry_traded_curr_group += 1

                    update_results(pair_one_group, pair_two_group, inter_industry_pairs_dict, total_payoffs)

                # Within industry
                else:
                    #within_industry_payoffs_series_curr.extend(returns[j][i])
                    within_industry_pairs.append(pair_list[group][pair])
                    within_industry_identified_curr_group += 1

                    if total_payoffs != 0:
                        within_industry_payoffs_curr_group += total_payoffs
                        within_industry_traded_curr_group += 1


            print("Group " + group)
            try:
                #return_on_committed_capital_dict[group].append((inter_industry_payoffs_curr_group + within_industry_payoffs_curr_group)/(inter_industry_identified_curr_group + within_industry_identified_curr_group))
                #fully_invested_return_dict[group].append((inter_industry_payoffs_curr_group + within_industry_payoffs_curr_group)/(inter_industry_traded_curr_group + within_industry_traded_curr_group))
                #print("Return on committed capital: " + str((inter_industry_payoffs_curr_group + within_industry_payoffs_curr_group)/(inter_industry_identified_curr_group + within_industry_identified_curr_group)))
                print("Fully invested return: " + str((inter_industry_payoffs_curr_group + within_industry_payoffs_curr_group)/(inter_industry_traded_curr_group + within_industry_traded_curr_group)))
                if group != "unclassified":
                    returns_list.append((inter_industry_payoffs_curr_group + within_industry_payoffs_curr_group)/(inter_industry_traded_curr_group + within_industry_traded_curr_group))
            except:
                #return_on_committed_capital_dict[group].append(0.00)
                #fully_invested_return_dict[group].append(0.00)
                #print("Return on committed capital: 0.00")
                print("Fully invested return: 0.00")
                #if group != "unclassified":
                    #returns_list.append(0.00)
                pass

            if model == "dbscan":
                #generate_heat_map(pairs_beta_dict, groups, "Average Beta for Group " + str(group) + " (" + str(year + 2003) + ")")
                generate_heat_map(pairs_payoffs_dict, groups, "Average Payoffs for Group " + str(group) + " (" + str(year + 2003) + ")")

            #print("\n")

        print(year)

        if model == "baseline":
            average = statistics.mean(returns_list)
            stdev = statistics.stdev(returns_list)

            print("Average: " + str(average))
            print("Standard Deviation: " + str(stdev))
            print("+ 1SD: " + str(average + stdev))
            print("- 1SD: " + str(average - stdev))
            print("Median: " + str(statistics.median(returns_list)))
            print("\n")


            #print("\nInter Industry pairs composition")
            #headers = ["Industries", "Count", "Average Payoffs"]
            #returns_list = [(k,) + v for k, v in pairs_payoffs_dict.items()]
            #sorted_list = sorted(returns_list, key=lambda x: x[2], reverse=True)
            #print(tabulate(sorted_list, headers=headers))


def update_results(pair_one_group, pair_two_group, results_dict, add_val, calc_average=False):

    if (pair_one_group, pair_two_group) in results_dict.keys():
        prev_count, prev_val = results_dict[(pair_one_group, pair_two_group)]
        new_count = prev_count + 1

        if calc_average:
            new_val = (prev_val * prev_count + add_val) / new_count
        else:
            new_val = prev_val + add_val
        results_dict[(pair_one_group, pair_two_group)] = (new_count, new_val)

    elif (pair_two_group, pair_one_group) in results_dict.keys():
        prev_count, prev_val = results_dict[(pair_two_group, pair_one_group)]
        new_count = prev_count + 1

        if calc_average:
            new_val = (prev_val * prev_count + add_val) / new_count
        else:
            new_val = prev_val + add_val
        results_dict[(pair_two_group, pair_one_group)] = (new_count, new_val)

    else:
        results_dict[(pair_one_group, pair_two_group)] = (1, add_val)


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

    plt.subplots(figsize=(50, 50))
    plt.tick_params(axis='both', labelsize=30)
    mask = np.zeros_like(consolidated_result, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True
    mask[np.diag_indices_from(mask)] = False

    ax = sns.heatmap(consolidated_result, mask=mask, xticklabels=list(groups.keys()), yticklabels=list(groups.keys()))
    # use matplotlib.colorbar.Colorbar object
    cbar = ax.collections[0].colorbar
    # here set the labelsize by 20
    cbar.ax.tick_params(labelsize=60)
    plt.show()


if __name__ == '__main__':
    pairs_dict, payoffs_per_pair_dict, payoffs_per_day_dict = populate_result.main(models)

    fully_invested_return_list = {}
    identified_pairs_list = {}
    traded_pairs_list = {}

    for model in models:
        print(model)
        analyse_pairs(pairs_dict[model], payoffs_per_pair_dict[model], payoffs_per_day_dict[model])
        print("\n")