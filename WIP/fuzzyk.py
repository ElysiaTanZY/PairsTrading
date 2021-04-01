import math
import skfuzzy as fuzz

from WIP import cointegration_test


def fuzzy_main(dataset, index_mapping, share_list, p_value=0.05):

    ''' Identifies pairs to be traded under the Fuzzy C-Means model

    :param dataset: Data set to be clustered
    :param index_mapping: Mapping of PERMNO to row in dataset
    :param share_list: List of shares to be considered during the formation period
    :param p_value: Cointegration threshold
    :return: Cointegrated pairs separated into their individual groups
    '''

    feature_set = dataset.drop(columns=['permno'])
    num_rows = feature_set.shape[0]
    num_dimensions = len(feature_set.columns)
    print(num_rows)
    print(num_dimensions)
    print(feature_set.columns)

    # Heuristic to determine Fuzzifier value adapted from A simple and fast method to determine the parameters for
    # fuzzy c-means cluster analysis by Schwammle and Jensen (2010)
    fuzzifier = 1 + (1418 / num_rows + 22.05)*num_dimensions**(-2) + (12.33/num_rows + 0.243)*num_dimensions**(-0.0406*math.log(num_rows) - 0.1134)

    max_fuzzy_partition_coefficient = -1.0
    optimal_num_clusters = 2

    fuzzy_partition_coefficient_list = []

    for i in range(2, 49):
        fuzzy_partition_coefficient = cluster_fuzzy(feature_set, i, fuzzifier)
        fuzzy_partition_coefficient_list.append(fuzzy_partition_coefficient)

        if fuzzy_partition_coefficient > max_fuzzy_partition_coefficient:
            max_fuzzy_partition_coefficient = fuzzy_partition_coefficient
            optimal_num_clusters = i

    membership = cluster_fuzzy(feature_set, optimal_num_clusters, fuzzifier, False)
    grouped_stocks = group_stocks(membership, index_mapping, share_list, dataset)
    return cointegration_test.main(grouped_stocks, p_value)


def group_stocks(membership, index_mapping, share_list, dataset):

    ''' Takes the output from the Fuzzy C-Means algorithm and groups shares into their corresponding groups

    :param membership: Output from the Fuzzy C-Means algorithm
    :param index_mapping: Mapping of PERMNO to row in dataset
    :param share_list: List of shares to be considered during the formation period
    :param dataset: Data set to be clustered
    :return: Grouped shares
    '''

    grouped_stocks = {}
    # Sum of membership in all groups add up to 1
    threshold = 1 / len(membership)

    for i in range(0, len(membership)):
        group = membership[i]
        grouped_stocks[str(i)] = []

        for j in range(0, len(group)):
            if group[j] > threshold:
                permno = dataset.iloc[j]['permno']
                index = index_mapping[str(int(permno))]

                temp = grouped_stocks[str(i)]
                temp.append((share_list[index][0], share_list[index][2], share_list[index][3], share_list[index][1]))
                grouped_stocks[str(i)] = temp

    return grouped_stocks


def cluster_fuzzy(feature_set, num_clusters, fuzzifier, is_searching=True):

    ''' Executes the Fuzzy C-Means algorithm

    :param feature_set: Data set to be clustered
    :param num_clusters: Number of clusters required
    :param fuzzifier: Level of cluster fuzziness
    :param isSearching: Indicator for whether the script is still searching for the optimal hyperparameters
    :return: Fuzzy Partition Coefficient if script is still searching, membership values otherwise
    '''

    cntr, membership, init_group, dist, objective_function, num_iter, partition_coefficient = fuzz.cluster.cmeans(
        feature_set.T, num_clusters, fuzzifier, error=0.005, maxiter=300, init=None)

    if is_searching:
        return partition_coefficient
    else:
        return membership
