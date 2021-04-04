from kneed import KneeLocator
import math
from matplotlib import pyplot as plt
import numpy as np
from sklearn import metrics
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

from Final import cointegration_test


def dbscan_main(dataset, index_mapping, share_list, p_value=0.05):

    ''' Identifies pairs to be traded under the DBSCAN model

    :param dataset: Data set to be clustered
    :param index_mapping: Mapping of PERMNO to row in dataset
    :param share_list: List of shares to be considered during the formation period
    :param p_value: Cointegration threshold
    :return: Cointegrated pairs separated into their individual groups and number of outliers identified
    '''

    feature_set = dataset.drop(columns=['permno'])
    num_rows = feature_set.shape[0]
    num_dimensions = len(feature_set.columns)

    print(num_rows)
    print(num_dimensions)
    print(feature_set.columns)

    max_silhouette_score = -2.0
    optimal_minPts = 0
    optimal_eps = 0.01

    # Heuristic for minPts taken from An algorithm for clustering spatial-temporal data by Birant and Kut (2007)
    for minPts in range(max(4, math.floor(math.log(num_rows)) - 5), math.floor(math.log(num_rows)) + 6):
        computed_eps = compute_optimal_eps(feature_set, minPts)

        for j in range(-20, 21):
            eps = (1 + j * 0.01) * computed_eps

            # eps needs to be positive
            if eps > 0:
                silhouette_score = cluster_dbscan(feature_set, minPts, eps)

                if silhouette_score > max_silhouette_score:
                    max_silhouette_score = silhouette_score
                    optimal_eps = eps
                    optimal_minPts = minPts

    labels = cluster_dbscan(feature_set, optimal_minPts, optimal_eps, False)
    grouped_stocks, num_outliers = group_stocks(labels, index_mapping, share_list, dataset)
    print(grouped_stocks)

    return cointegration_test.main(grouped_stocks, p_value), num_outliers


def group_stocks(labels, index_mapping, share_list, dataset):

    ''' Takes the output from the DBSCAN algorithm and groups shares into their corresponding groups

    :param labels: Output from the DBSCAN algorithm
    :param index_mapping: Mapping of PERMNO to row in dataset
    :param share_list: List of shares to be considered during the formation period
    :param dataset: Data set to be clustered
    :return: Grouped shares and number of outliers identified
    '''

    grouped_stocks = {}
    num_outliers = 0

    for i in range(0, len(labels)):
        label = str(labels[i])
        permno = dataset.iloc[i]['permno']

        index = index_mapping[str(int(permno))]

        # DBSCAN labels outlier points as -1
        if not label == '-1':
            if label not in grouped_stocks.keys():
                grouped_stocks[label] = [(share_list[index][0], share_list[index][2], share_list[index][3], share_list[index][1])]
            else:
                temp = grouped_stocks[label]
                temp.append((share_list[index][0], share_list[index][2], share_list[index][3], share_list[index][1]))
                grouped_stocks[label] = temp
        else:
            num_outliers += 1

    return grouped_stocks, num_outliers


def compute_optimal_eps(feature_set, minPts):

    ''' Computes optimal eps based on heuristic in A density-based algorithm for discovering clusters in large spatial
        # databases with noise by Sander, Ester, Kriegel and Xu (1996)

    :param feature_set: Data set to be clustered
    :param minPts: Number of points that need to be in the neighbourhood of a given point for it to be considered core
    :return: Optimal eps
    '''

    neighbours = NearestNeighbors(n_neighbors=minPts, metric='manhattan')
    neighbours_fit = neighbours.fit(feature_set)
    distances, indices = neighbours_fit.kneighbors(feature_set)

    distances = np.sort(distances, axis=0)
    sorted_distances = distances[:,1]
    sorted_distances = sorted_distances[::-1]
    plt.plot(sorted_distances)

    derivative = [0]
    for i in range(1, len(sorted_distances)):
        derivative.append(sorted_distances[i] - sorted_distances[i-1])

    kneedle = KneeLocator(distances[:, 1], sorted_distances, S=1.0, direction='decreasing')
    print(kneedle.knee_y)
    return kneedle.knee_y


def cluster_dbscan(feature_set, minPts, eps, is_searching=True):

    ''' Executes the DBSCAN algorithm

    :param feature_set: Data set to be clustered
    :param minPts: Number of points that need to be in the neighbourhood of a given point for it to be considered core
    :param eps: Neighbourhood size
    :param is_searching: Indicator for whether the script is still searching for the optimal hyperparameters
    :return: Silhouette score if script is still searching, output labels otherwise
    '''

    clustering = DBSCAN(eps=eps, min_samples=minPts, metric='manhattan').fit(feature_set)
    labels = clustering.labels_

    # Measure Performance
    core_samples = np.zeros_like(labels, dtype=bool)
    core_samples[clustering.core_sample_indices_] = True

    # Calculate number of clusters
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    # Compute silhouette score
    try:
        silhouette_score = metrics.silhouette_score(feature_set, labels)
    except:
        silhouette_score = -1

    print('Silhouette Score:' + str(silhouette_score))

    if is_searching:
        return silhouette_score

    print(len(set(labels)))
    print(str(n_clusters))
    return labels
