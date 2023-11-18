"""
clustering: Use scikit-learn "AgglomerativeClustering" model for clustering a set of distribution centers.

The aim is to select a predefined number of *candidates* for implementing
a distribution center. Data are:

  - number of candidates to select
  - customer locations
  - potential distribution center locations
  - plant locations

See `TestClustering` below for examples of usage.
"""

import random
import unittest
import numpy as np
import pandas as pd
from geopy.distance import great_circle as distance
from sklearn.cluster import AgglomerativeClustering


def preclustering(cust, dc, prods, demand, n_clusters):
    """
    Clustering as a predecessor for optimization, to be used in logistics network design

    :param cust: Dictionary associating a customer id to its location as (latitute, longitude)
    :param dc: Dictionary associating a distribution center id to its (latitute, longitude)
    :param prods: List (set) of products
    :param demand: Demand[k, p] -> units of `p` demanded by customer `k`
    :param n_clusters: Number of clusters to use

    :return: List of selected dc's (a subset of `dc`)
    """
    key_dc = list(dc.keys())
    n_dc = len(key_dc)

    # Compute distances between distribution centers
    d = np.zeros((n_dc, n_dc), np.int)
    for i in range(n_dc):
        for j in range(i, n_dc):
            d[i, j] = distance(dc[key_dc[i]], dc[key_dc[j]]).kilometers + 0.5
            d[j, i] = d[i, j]

    # Assign customer demand to the closest distribution center using a simple heuristic
    dc_dem = np.zeros((n_dc,), np.int)
    for z in cust:
        dists = np.array([distance(cust[z], dc[k]).kilometers + 0.5 for k in key_dc], np.int)
        imin = np.argmin(dists)
        dc_dem[imin] += sum(demand[z, p] for p in prods)

    # Apply hierarchical agglomerative clustering
    model = AgglomerativeClustering(linkage='average', affinity='precomputed', n_clusters=n_clusters)
    model.fit(d)

    # Choose the distribution center with the highest demand in each cluster
    cluster_dc = []
    for i in range(n_clusters):
        indices = np.where(model.labels_ == i)[0]
        demands = [dc_dem[j] for j in indices]
        dmax = np.argmax(demands)
        cluster_dc.append(indices[dmax])

    return [key_dc[i] for i in cluster_dc]



