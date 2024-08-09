from logging_utils.logging_utils import log_timed

import json
import mmap

import orjson
import os
import sys
import numpy as np
import concurrent.futures
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score



@log_timed()
def get_data_from_json(filepath):
    assert os.path.isfile(filepath), f"No file found at {filepath}"
    try:
        with open(filepath, 'r') as f:
            return orjson.loads(f.read())
            # for very large files, this is faster than json.load
            # with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            #     return orjson.loads(mm.read(mm.size()))
    except FileNotFoundError as e:
        sys.exit(f"Could not find {filepath}")


def extract_function_names(file):
    rank_data_df = pd.read_json(file)
    return np.unique(rank_data_df['name'].to_numpy())


@log_timed()
def get_unique_function_names(files: list[str], function_pattern_to_keep: str = None,
                              function_pattern_to_drop: str = None):
    function_names = set()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(extract_function_names, files, chunksize=10)
        for result in results:
            function_names.update(result)

    if function_pattern_to_keep is not None:
        function_names = {name for name in function_names if function_pattern_to_keep in name}
    if function_pattern_to_drop is not None:
        function_names = {name for name in function_names if function_pattern_to_drop not in name}

    function_names = {name for name in function_names if name}

    return function_names


def load_rank_data(file_name_template, rank):
    return rank, get_data_from_json(file_name_template.format(rank))


@log_timed()
def create_feature_dataframe(file_name_template: str, ranks: list[int], function_names: list[str]):
    columns = [f'{name}_{stat}' for name in function_names for stat in
               ['duration_min', 'duration_q1', 'duration_q2', 'duration_avg', 'duration_sum', 'duration_q3', 'duration_max', 'n_calls']]

    data = {f'rank {rank}': {col: 0.0 for col in columns} for rank in ranks}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        rank_data_futures = {executor.submit(load_rank_data, file_name_template, rank): rank for rank in ranks}
        for future in concurrent.futures.as_completed(rank_data_futures):
            rank, rank_data = future.result()
            for function_name in function_names:
                function_durations = [event['dur'] for event in rank_data if event['name'] == function_name]
                if function_durations:
                    data[f'rank {rank}'][f'{function_name}_duration_min'] = np.min(function_durations)
                    data[f'rank {rank}'][f'{function_name}_duration_q1'] = np.percentile(function_durations, 25)
                    data[f'rank {rank}'][f'{function_name}_duration_q2'] = np.percentile(function_durations, 50)
                    data[f'rank {rank}'][f'{function_name}_duration_avg'] = np.average(function_durations)
                    data[f'rank {rank}'][f'{function_name}_duration_sum'] = np.sum(function_durations)
                    data[f'rank {rank}'][f'{function_name}_duration_q3'] = np.percentile(function_durations, 75)
                    data[f'rank {rank}'][f'{function_name}_duration_max'] = np.max(function_durations)
                    data[f'rank {rank}'][f'{function_name}_n_calls'] = len(function_durations)

    df = pd.DataFrame.from_dict(data, orient='index', columns=columns)
    df.index.name = 'rank'

    return df


@log_timed()
def scale_dataframe(df: pd.DataFrame):
    scaler = StandardScaler()

    df_scaled = scaler.fit_transform(df)

    df_scaled = pd.DataFrame(df_scaled, columns=df.columns)
    df_scaled.index = df.index

    return df_scaled


@log_timed()
def apply_pca(df: pd.DataFrame):
    pca = PCA()
    df_scaled_pca = pca.fit_transform(df)
    cumulative_sum = np.cumsum(pca.explained_variance_ratio_)
    for index, sum_value in enumerate(cumulative_sum):
        if sum_value > 0.95:
            n_components_for_95_pct_variance = index + 1
            break
    df_scaled_pca = pca.fit_transform(df)
    data_scaled_pca_df = pd.DataFrame(df_scaled_pca[:, :n_components_for_95_pct_variance],
                                      columns=[f'PCA {i}' for i in range(n_components_for_95_pct_variance)])
    data_scaled_pca_df.index = df.index

    features = df.columns

    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)

    loadings_df = pd.DataFrame(loadings[:, :n_components_for_95_pct_variance], index=features,
                               columns=[f'PCA {i}' for i in range(n_components_for_95_pct_variance)])

    return data_scaled_pca_df, loadings_df


@log_timed()
def apply_kmeans(
        df: pd.DataFrame,
        n_ranks: int
):
    silhouette = []
    # @todo: add more logic here to avoid doing too much kmeans for large numbers of ranks
    for n_clusters in range(2, 5):
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(df)
        score = silhouette_score(df, kmeans.labels_)
        print(f'  KMeans: {n_clusters} clusters -> silhouette score: {score}')
        silhouette.append(score)
    if np.max(silhouette) < 0.5:
        print(f"Silhouette scores are low: {silhouette}")
        n_clusters = 1
        kmeans = None
        df = df.assign(cluster=0)
    else:
        # get number of clusters that maximizes the silhouette score
        n_clusters = np.argmax(silhouette) + 2  # +2 because the first number of clusters we test is 2
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(df)
        df['cluster'] = kmeans.labels_
    return kmeans, n_clusters, df


@log_timed()
def get_representative_ranks_of_clusters(
        df: pd.DataFrame,
        kmeans: KMeans,
        ranks: list[int]
):
    centroids = kmeans.cluster_centers_
    # print(centroids)
    representative_ranks = {}
    n_pca_components = len(df.columns) - 2
    # print(n_pca_components)
    # print(df)
    for cluster, cluster_centroid in enumerate(centroids):
        # print(f"Looking at cluster {cluster}")
        # print(f"cluster centroid: {cluster_centroid}")
        # get ranks in this cluster
        cluster_ranks = df[df['cluster'] == cluster]
        # print(f"cluster ranks: {cluster_ranks}")
        distances = []
        # get distance from each rank to the centroid
        for rank in cluster_ranks.index:
            # print(f"  - Looking at rank {rank}")
            rank_data = df.loc[f'{rank}', :].to_numpy()
            # drop the cluster column
            rank_data = rank_data[:-1]
            # print(f"    rank data: {rank_data}")
            distance = np.linalg.norm(rank_data - cluster_centroid)
            # print(f"    distance: {distance}")
            distances.append(distance)
        print(distances)
        # get rank with minimum distance
        min_distance_index = np.argmin(distances)
        # print(min_distance_index)
        # print(cluster_ranks.index)
        # print(cluster_ranks.index[min_distance_index])
        representative_ranks[f"cluster {cluster}"] = cluster_ranks.index[min_distance_index]

    return representative_ranks
