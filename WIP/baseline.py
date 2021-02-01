import json
import pandas as pd
import cointegration_test


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
                        update_groups(groups, group, relevant_shares, i)
                        is_grouped = True
                        break

                if is_grouped:
                    break

    return groups


def update_groups(groups, name, relevant_shares, index):
    if name not in groups.keys():
        groups[name] = [(relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3])]
    else:
        temp = groups[name]
        temp.append((relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3]))
        groups[name] = temp


def main(data, relevant_shares):
    # Formation period: 3 years + Trading period: 1 year (Rolling basis)
    print("Forming pairs")
    grouped_shares = group_shares(relevant_shares)
    cointegrated_pairs = cointegration_test.main(grouped_shares)
    #return ranked_pairs
    return cointegrated_pairs


if __name__ == '__main__':
    with open('/Backup/chosen_shares_copy.json') as json_file:
        shares = json.load(json_file)

    date_cols = ['date']
    data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv", parse_dates=date_cols)

    grouped_shares = group_shares(shares)
    cointegrated_pairs = cointegration_test.main(grouped_shares, data)

