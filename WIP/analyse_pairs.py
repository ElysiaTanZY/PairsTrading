import json
import matplotlib.pyplot as plt
from tabulate import tabulate
from WIP import analyse_returns


def main(pair_list, returns):
    analyse_pairs(pair_list, returns)   # returns: [[[(payoffs, date)]]]


def analyse_pairs(pair_lists, returns):
    # [(permno_one, trade_start_one_row, permno_two, trade_start_two_row, mean, std, beta, sic_one, sic_two)]
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        groups = json.load(json_file)

    inter_industry_pairs = []    # List of all inter industry pairs across all years
    within_industry_pairs = []   # List of all within industry pairs across all years

    payoffs_inter_industry = []      # List of payoffs generated by inter industry pairs each year
    payoffs_within_industry = []     # List of payoffs generated by within industry pairs each year

    #payoffs_series_inter_industry = []  # List of payoffs series generated by inter industry pairs each year
    #payoffs_series_within_industry = []  # List of payoffs series generated by within industry pairs each year

    traded_inter_industry = []  # List of traded inter industry pairs each year
    traded_within_industry = []  # List of traded within industry pairs each year

    identified_inter_industry = []  # List of identified inter industry pairs each year
    identified_within_industry = []  # List of identified within industry pairs each year

    inter_industry_pairs_dict = {}  # Splits the inter-indsutry pairs into their respective group pair

    for j in range(0, len(pair_lists)):
        pair_list = pair_lists[j]

        if len(pair_list) != len(returns[j]):
            print("Something wrong")
            return

        inter_industry_payoffs_curr_year = 0
        within_industry_payoffs_curr_year = 0

        inter_industry_payoffs_series_curr = []
        within_industry_payoffs_series_curr = []

        inter_industry_traded_curr_year = 0
        within_industry_traded_curr_year = 0

        inter_industry_identified_curr_year = 0
        within_industry_identified_curr_year = 0

        for i in range(0, len(pair_list)):
            sic_one = int(pair_list[i][7])
            sic_two = int(pair_list[i][8])

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

            total_payoffs = sum(returns[j][i])

            if pair_one_group != pair_two_group:
                #inter_industry_payoffs_series_curr.extend(returns[j][i])
                inter_industry_pairs.append(pair_list[i])
                inter_industry_identified_curr_year += 1

                if total_payoffs != 0:
                    inter_industry_payoffs_curr_year += total_payoffs
                    inter_industry_traded_curr_year += 1

                if (pair_one_group, pair_two_group) not in inter_industry_pairs_dict.keys():
                    inter_industry_pairs_dict[(pair_one_group, pair_two_group)] = (1, total_payoffs)
                else:
                    prev_count, prev_average = inter_industry_pairs_dict[(pair_one_group, pair_two_group)]
                    new_count = prev_count + 1
                    new_average = (prev_average * prev_count + total_payoffs) / new_count
                    inter_industry_pairs_dict[(pair_one_group, pair_two_group)] = (new_count, new_average)

            else:
                #within_industry_payoffs_series_curr.extend(returns[j][i])
                within_industry_pairs.append(pair_list[i])
                within_industry_identified_curr_year += 1

                if total_payoffs != 0:
                    within_industry_payoffs_curr_year += total_payoffs
                    within_industry_traded_curr_year += 1

        payoffs_inter_industry.append(inter_industry_payoffs_curr_year)
        payoffs_within_industry.append(within_industry_payoffs_curr_year)

        traded_inter_industry.append(inter_industry_traded_curr_year)
        traded_within_industry.append(within_industry_traded_curr_year)

        identified_inter_industry.append(inter_industry_identified_curr_year)
        identified_within_industry.append(within_industry_identified_curr_year)

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

    print("\nInter-Industry Pairs Analysis:")
    analyse_returns.analyse_returns(payoffs_inter_industry, traded_inter_industry, identified_inter_industry)

    print("\nWithin-Industry Pairs Analysis:")
    analyse_returns.analyse_returns(payoffs_within_industry, traded_within_industry, identified_within_industry)

    generate_heat_map(pair_list, returns, groups)


def generate_heat_map(pair_lists, groups):
    groups_dict = {}   # Map the group to an index
    count = 0

    for group, value in groups:
        groups_dict[group] = count
        count += 1

    consolidated_result = []

    for i in range(0, count):
        group_result = []
        for j in range(0, count):
            group_result.append(0)
        consolidated_result.append(group_result)

    for i in range(0, len(pair_lists)):
        pair_list = pair_lists[i]



if __name__ == '__main__':
    pass