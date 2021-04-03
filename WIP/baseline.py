import json

from WIP import cointegration_test


def main(relevant_shares):

    ''' Identifies pairs to be traded under the Baseline model

    :param relevant_shares: Shares to be considered in the formation period
    :return: Cointegrated pairs separated into their individual groups and number of unclassified shares
    '''

    print("Forming pairs")
    grouped_shares, num_unclassified = group_shares(relevant_shares)
    cointegrated_pairs = cointegration_test.main(grouped_shares)
    return cointegrated_pairs, num_unclassified


def group_shares(relevant_shares):

    ''' Groups shares according to industry group based on the Fama French classification

    :param relevant_shares: Shares to be considered in the formation period
    :return: Grouped shares and number of unclassified shares
    '''

    # Adapted from: https://github.com/alexchinco/CRSP-Data-Summary-Statistics-by-Industry-/blob/master/industries.json
    with open('/Users/elysiatan/PycharmProjects/thesis/fama_french.json') as json_file:
        data = json.load(json_file)

    groups = {}
    num_unclassified = 0

    for i in range(0, len(relevant_shares)):
        sic_code = relevant_shares[i][1]
        if str(sic_code).isalpha():
            sic_code = int(9999)
        else:
            sic_code = int(sic_code)

        if sic_code == 9999:
            num_unclassified += 1

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

    return groups, num_unclassified


def update_groups(groups, name, relevant_shares, index):

    ''' Adds a share to its group

    :param groups: Group share should be added to
    :param name: PERMNO of share to be added
    :param relevant_shares: Shares to be considered in the formation period
    :param index: Index of share to be added in relevant_shares
    :return:
    '''

    if name not in groups.keys():
        groups[name] = [(relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3], relevant_shares[index][1])]
    else:
        temp = groups[name]
        temp.append((relevant_shares[index][0], relevant_shares[index][2], relevant_shares[index][3], relevant_shares[index][1]))
        groups[name] = temp


if __name__ == '__main__':
    pass

