from kneed import KneeLocator
from matplotlib import pyplot as plt
from sklearn import metrics
from sklearn_extra.cluster import KMedoids

import cointegration_test


def kmedoid_main(dataset, index_mapping, share_list):
    feature_set = dataset.drop(columns=['permno'])
    num_rows = feature_set.shape[0]
    num_dimensions = len(feature_set.columns)
    print(num_rows)
    print(num_dimensions)
    print(feature_set.columns)

    initial_num_clusters = compute_initial_num_clusters(feature_set)

    max_silhouette_score = -2.0
    optimal_num_clusters = 2

    for i in range(max(2, initial_num_clusters - 5), initial_num_clusters + 6):
        silhouette_score = cluster_kmedoids(feature_set, i)

        if silhouette_score > max_silhouette_score:
            max_silhouette_score = silhouette_score
            optimal_num_clusters = i

    labels = cluster_kmedoids(feature_set, optimal_num_clusters, False)
    grouped_stocks = group_stocks(labels, index_mapping, share_list, dataset)
    return cointegration_test.main(grouped_stocks)


def group_stocks(labels, index_mapping, share_list, dataset):
    grouped_stocks = {}
    for i in range(0, len(labels)):
        label = labels[i]
        permno = dataset.iloc[i]['permno']

        index = index_mapping[str(int(permno))]

        if not label == -1:
            if label not in grouped_stocks.keys():
                grouped_stocks[label] = [(share_list[index][0], share_list[index][2], share_list[index][3])]
            else:
                temp = grouped_stocks[label]
                temp.append((share_list[index][0], share_list[index][2], share_list[index][3]))
                grouped_stocks[label] = temp

    return grouped_stocks


def compute_initial_num_clusters(feature_set):
    inertia = [] # KMedoids inertia is the sum of distances of samples to their closest cluster center

    for i in range(2, 49):
        kmedoids = KMedoids(n_clusters=i, init='heuristic', metric='manhattan').fit(feature_set)
        inertia.append(kmedoids.inertia_)

    plt.plot(range(2, 49), inertia)
    plt.show()

    kneedle = KneeLocator(range(2, 49), inertia, S=1.0, direction='decreasing')
    print(kneedle.knee)
    return kneedle.knee


def cluster_kmedoids(feature_set, num_clusters, is_searching=True):
    kmedoids = KMedoids(n_clusters=num_clusters, init='heuristic', metric='manhattan').fit(feature_set)
    labels = kmedoids.labels_

    silhouette_score = metrics.silhouette_score(feature_set, labels)
    print('Silhouette Score: ' + str(silhouette_score))

    if is_searching:
        return silhouette_score
    else:
        print(len(labels))
        return labels