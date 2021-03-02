from kneed import KneeLocator
from matplotlib import pyplot as plt

import numpy as np
import math
import cointegration_test
import skfuzzy as fuzz

colors = ['b', 'orange', 'g', 'r', 'c', 'm', 'y', 'k', 'Brown', 'ForestGreen']


def fuzzy_main(dataset, index_mapping, share_list):
    feature_set = dataset.drop(columns=['permno'])
    num_rows = feature_set.shape[0]
    num_dimensions = len(feature_set.columns)
    print(num_rows)
    print(num_dimensions)
    print(feature_set.columns)

    # A simple and fast method to determine the parameters for fuzzy c-means cluster analysis (Schwammle and Jensen, 2010)
    fuzzifier = 1 + (1418 / num_rows + 22.05)*num_dimensions**(-2) + (12.33/num_rows + 0.243)*num_dimensions**(-0.0406*math.log(num_rows) - 0.1134)

    #initial_num_clusters = compute_initial_num_clusters(feature_set, fuzzifier)
    initial_num_clusters = 2
    max_fuzzy_partition_coefficient = -1.0
    optimal_num_clusters = 2

    fuzzy_partition_coefficient_list = []

    for i in range(2, 49):
        fuzzy_partition_coefficient = cluster_fuzzy(feature_set, i, fuzzifier)
        fuzzy_partition_coefficient_list.append(fuzzy_partition_coefficient)

        if fuzzy_partition_coefficient > max_fuzzy_partition_coefficient:
            max_fuzzy_partition_coefficient = fuzzy_partition_coefficient
            optimal_num_clusters = i

    plt.plot(range(2, 49), fuzzy_partition_coefficient_list)
    plt.show()

    membership = cluster_fuzzy(feature_set, optimal_num_clusters, fuzzifier, False)
    grouped_stocks = group_stocks(membership, index_mapping, share_list, dataset)
    return cointegration_test.main(grouped_stocks)


def group_stocks(membership, index_mapping, share_list, dataset):
    grouped_stocks = {}
    threshold = 1 / len(membership) # Sum of membership in all groups add up to 1

    for i in range(0, len(membership)):
        group = membership[i]
        grouped_stocks[i] = []

        for j in range(0, len(group)):
            if group[j] > threshold:
                permno = dataset.iloc[j]['permno']
                index = index_mapping[str(int(permno))]

                temp = grouped_stocks[i]
                temp.append((share_list[index][0], share_list[index][2], share_list[index][3], share_list[index][1]))
                grouped_stocks[i] = temp

    return grouped_stocks


def cluster_fuzzy(feature_set, num_clusters, fuzzifier, is_searching=True):
    cntr, membership, init_group, dist, objective_function, num_iter, partition_coefficient = fuzz.cluster.cmeans(
        feature_set.T, num_clusters, fuzzifier, error=0.005, maxiter=300, init=None)

    if is_searching:
        return partition_coefficient
    else:
        return membership
