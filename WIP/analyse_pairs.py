import json
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
from WIP import analyse_returns


def main(pair_list, returns, payoffs_per_day):
    analyse_pairs(pair_list, returns, payoffs_per_day)   # returns: [[[(payoffs, start, end, start, end)]]]


def analyse_pairs(pair_lists, returns, payoffs_per_day):
    # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta, sic_one, sic_two)]
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        groups = json.load(json_file)

    inter_industry_pairs = []    # List of all inter industry pairs across all years
    within_industry_pairs = []   # List of all within industry pairs across all years

    payoffs_inter_industry = []      # List of payoffs generated by inter industry pairs each year
    payoffs_within_industry = []     # List of payoffs generated by within industry pairs each year
    payoffs_combined = []
    #payoffs_series_inter_industry = []  # List of payoffs series generated by inter industry pairs each year
    #payoffs_series_within_industry = []  # List of payoffs series generated by within industry pairs each year

    traded_inter_industry = []  # List of traded inter industry pairs each year
    traded_within_industry = []  # List of traded within industry pairs each year
    traded_combined = []

    identified_inter_industry = []  # List of identified inter industry pairs each year
    identified_within_industry = []  # List of identified within industry pairs each year
    identified_combined = []

    inter_industry_pairs_dict = {}  # Splits the inter-indsutry pairs into their respective group pair
    pairs_dict = {}    # Store the groups of chosen pairs
    payoffs_dict = {}   # Store the returns of chosen pairs separated by industry

    for year in range(0, len(pair_lists)):
        pair_list = pair_lists[year]

        if len(pair_list) != len(returns[year]):
            print("Something wrong")
            return

        inter_industry_payoffs_curr_year = 0
        within_industry_payoffs_curr_year = 0

        inter_industry_traded_curr_year = 0
        within_industry_traded_curr_year = 0

        inter_industry_identified_curr_year = 0
        within_industry_identified_curr_year = 0

        for pair in range(0, len(pair_list)):
            sic_one = int(pair_list[pair][7])
            sic_two = int(pair_list[pair][8])

            is_identified_group_one = False
            is_identified_group_two = False

            for group, value in groups.items():
                for sub_group, index in value.items():
                    start = int(index['start'])
                    end = int(index['end'])

                    if start <= sic_one <= end:
                        pair_one_group = group
                        is_identified_group_one = True

                    if start <= sic_two <= end:
                        pair_two_group = group
                        is_identified_group_two = True

                    if is_identified_group_one and is_identified_group_two:
                        break

                if is_identified_group_one and is_identified_group_two:
                    break

            total_payoffs = sum(x[0] for x in returns[year][pair])

            update_results(pair_one_group, pair_two_group, pairs_dict, pair_list[pair][9])
            update_results(pair_one_group, pair_two_group, payoffs_dict, total_payoffs)

            # Inter-industry
            if pair_one_group != pair_two_group:
                #inter_industry_payoffs_series_curr.extend(returns[j][i])
                inter_industry_pairs.append(pair_list[pair])
                inter_industry_identified_curr_year += 1

                if total_payoffs != 0:
                    inter_industry_payoffs_curr_year += total_payoffs
                    inter_industry_traded_curr_year += 1
                    print(returns[year][pair])

                update_results(pair_one_group, pair_two_group, inter_industry_pairs_dict, total_payoffs)

            # Within industry
            else:
                #within_industry_payoffs_series_curr.extend(returns[j][i])
                within_industry_pairs.append(pair_list[pair])
                within_industry_identified_curr_year += 1

                if total_payoffs != 0:
                    within_industry_payoffs_curr_year += total_payoffs
                    within_industry_traded_curr_year += 1
                    returns.append(returns[year][pair])

        payoffs_inter_industry.append(inter_industry_payoffs_curr_year)
        payoffs_within_industry.append(within_industry_payoffs_curr_year)
        payoffs_combined.append(inter_industry_payoffs_curr_year + within_industry_payoffs_curr_year)

        traded_inter_industry.append(inter_industry_traded_curr_year)
        traded_within_industry.append(within_industry_traded_curr_year)
        traded_combined.append(inter_industry_traded_curr_year + within_industry_traded_curr_year)

        identified_inter_industry.append(inter_industry_identified_curr_year)
        identified_within_industry.append(within_industry_identified_curr_year)
        identified_combined.append(inter_industry_identified_curr_year + within_industry_identified_curr_year)

        #payoffs_series_inter_industry.append(inter_industry_payoffs_series_curr)
        #payoffs_series_within_industry.append(within_industry_payoffs_series_curr)


    labels = 'inter-industry', 'within-industry'
    sizes = [len(inter_industry_pairs), len(within_industry_pairs)]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.axis('equal')
    plt.title('Pairs composition')
    plt.show()

    '''
    sizes = [sum(payoffs_inter_industry), sum(payoffs_within_industry)]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.axis('equal')
    plt.title('Pairs payoffs composition')
    plt.show()
    '''

    print("\nInter Industry pairs composition")
    headers = ["Industries", "Count", "Average Payoffs"]
    returns_list = [(k,) + v for k, v in inter_industry_pairs_dict.items()]
    sorted_list = sorted(returns_list, key=lambda x:x[2], reverse=True)
    print(tabulate(sorted_list, headers=headers))

    payoffs_per_day_inter_industry = []  # List of payoffs generated by inter industry pairs each year for MDD calculation
    payoffs_per_day_within_industry = []  # List of payoffs generated by within industry pairs each year for MDD calculation

    for year in range(0, len(payoffs_per_day)):
        payoffs_per_day_inter_industry_curr = [0] * len(payoffs_per_day[year])
        payoffs_per_day_within_industry_curr = [0] * len(payoffs_per_day[year])

        for day in range(0, len(payoffs_per_day[year])):
            for payoff in range(0, len(payoffs_per_day[year][day])):
                payoff_pair, sic_one, sic_two = payoffs_per_day[year][day][payoff]
                is_identified_group_one = False
                is_identified_group_two = False

                for group, value in groups.items():
                    for sub_group, index in value.items():
                        start = int(index['start'])
                        end = int(index['end'])

                        if start <= int(sic_one) <= end:
                            pair_one_group = group
                            is_identified_group_one = True

                        if start <= int(sic_two) <= end:
                            pair_two_group = group
                            is_identified_group_two = True

                        if is_identified_group_one and is_identified_group_two:
                            break

                    if is_identified_group_one and is_identified_group_two:
                        break

                if pair_one_group == pair_two_group:
                    payoffs_per_day_within_industry_curr[day] += int(payoff_pair)
                else:
                    payoffs_per_day_inter_industry_curr[day] += int(payoff_pair)

        payoffs_per_day_inter_industry.append(payoffs_per_day_inter_industry_curr)
        payoffs_per_day_within_industry.append(payoffs_per_day_within_industry_curr)

    print("\nInter-Industry Pairs Analysis:")
    analyse_returns.analyse_returns(payoffs_inter_industry, traded_inter_industry, identified_inter_industry)

    print("\nWithin-Industry Pairs Analysis:")
    analyse_returns.analyse_returns(payoffs_within_industry, traded_within_industry, identified_within_industry)

    print("\nAll:")
    analyse_returns.analyse_returns(payoffs_combined, traded_combined, identified_combined)

    generate_heat_map(pairs_dict, groups, "Average Beta")
    generate_heat_map(payoffs_dict, groups, "Average Payoffs")


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
    pass