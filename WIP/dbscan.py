from kneed import KneeLocator
from matplotlib import pyplot as plt
from sklearn import metrics
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

import cointegration_test

import numpy as np
import math


def dbscan_main(dataset, index_mapping, share_list):
    feature_set = dataset.drop(columns=['permno'])
    num_rows = feature_set.shape[0]
    num_dimensions = len(feature_set.columns)
    print(num_rows)
    print(num_dimensions)
    print(feature_set.columns)

    max_silhouette_score = -2.0
    optimal_minPts = 0
    optimal_eps = 0

    # https://medium.com/@tarammullin/dbscan-parameter-estimation-ff8330e3a3bd
    for minPts in range(max(4, math.floor(math.log(num_rows)) - 5), math.floor(math.log(num_rows) + 6)):
        print("Hello I am trying to compute eps next")
        computed_eps = compute_optimal_eps(feature_set, minPts)

        for j in range(-20, 21):
            eps = (1 + j * 0.01) * computed_eps
            silhouette_score = cluster_dbscan(feature_set, minPts, eps)

            if silhouette_score > max_silhouette_score:
                max_silhouette_score = silhouette_score
                optimal_eps = eps
                optimal_minPts = minPts

    labels = cluster_dbscan(feature_set, optimal_minPts, optimal_eps, False)
    grouped_stocks = group_stocks(labels, index_mapping, share_list, dataset)
    #print(grouped_stocks)
    return cointegration_test.main(grouped_stocks)


def group_stocks(labels, index_mapping, share_list, dataset):
    grouped_stocks = {}
    for i in range(0, len(labels)):
        label = labels[i]
        permno = dataset.iloc[i]['permno']

        index = index_mapping[str(int(permno))]

        if not label == -1:
            if label not in grouped_stocks.keys():
                grouped_stocks[label] = [(share_list[index][0], share_list[index][2], share_list[index][3], share_list[index][1])]
            else:
                temp = grouped_stocks[label]
                temp.append((share_list[index][0], share_list[index][2], share_list[index][3], share_list[index][1]))
                grouped_stocks[label] = temp

    return grouped_stocks


def compute_optimal_eps(feature_set, minPts):
    # Determination of Optimal Epsilon (Eps) Value on DBSCAN Algorithm to Clustering Data on Peatland Hotspots in Sumatra
    neighbours = NearestNeighbors(n_neighbors=minPts, metric='manhattan')
    neighbours_fit = neighbours.fit(feature_set)
    distances, indices = neighbours_fit.kneighbors(feature_set)

    distances = np.sort(distances, axis=0)
    sorted_distances = distances[:,1]
    sorted_distances = sorted_distances[::-1]
    plt.plot(sorted_distances)
    plt.show()

    derivative = [0]
    for i in range(1, len(sorted_distances)):
        derivative.append(sorted_distances[i] - sorted_distances[i-1])
    '''
    second_derivative = []
    for i in range(1, len(derivative)):
        second_derivative.append(derivative[i] - derivative[i-1])

    index = 0
    max_change = second_derivative[0]
    for i in range(1, len(second_derivative)):
        if second_derivative[i] > max_change:
            index = i
            max_change = second_derivative[i]
    '''
    kneedle = KneeLocator(distances[:, 1], sorted_distances, S=1.0, direction='decreasing')
    print(kneedle.knee_y)
    return kneedle.knee_y

    '''
    second_derivative = []
    #second_derivative.append(abs(sorted_distances[1] - 2 * sorted_distances[0]))
    second_derivative.append(0)

    for i in range(1, len(sorted_distances) - 1):
        second_derivative.append(abs(sorted_distances[i + 1] + sorted_distances[i - 1] - 2 * sorted_distances[i]))

    #second_derivative.append(abs(sorted_distances[len(sorted_distances) - 2] - 2 * sorted_distances[len(sorted_distances) - 1]))
    second_derivative.append(0)
    max = second_derivative[1]
    index = 1

    for i in range(2, len(second_derivative) -1):
        if second_derivative[i] > max:
            max = second_derivative[i]
            index = i

    print(sorted_distances[index])
    return sorted_distances[index]
    '''


def cluster_dbscan(feature_set, minPts, eps, isSearching=True):
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
        return -2

    print('Silhouette Score:' + str(silhouette_score))

    if isSearching:
        return silhouette_score

    print(len(set(labels)))
    print(str(n_clusters))

    '''
    # Plot clusters
    unique_labels = set(labels)
    colors = [plt.cm.Spectral(each)
              for each in np.linspace(0, 1, len(unique_labels))]

    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = [0, 0, 0, 1]

        class_member_mask = (labels == k)

        xy = feature_set[class_member_mask & core_samples]
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                 markeredgecolor='k', markersize=14)

        xy = feature_set[class_member_mask & ~core_samples]
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                 markeredgecolor='k', markersize=6)

    plt.title('Estimated number of clusters: %d' % n_clusters)
    plt.show()
    '''
    return labels
