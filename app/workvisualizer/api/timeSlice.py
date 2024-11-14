import json
import os
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from sklearn.cluster import HDBSCAN

import orjson

from logging_utils.logging_utils import log_timed

@log_timed()
def prepare_data_for_rank(file_name_template: str, rank: int):
    filepath = file_name_template.format(rank)
    assert os.path.isfile(filepath), f"No file found at {filepath}"
    try:
        rank_data_df = pd.read_json(filepath)
    except FileNotFoundError as e:
        sys.exit(f"Could not find {filepath}")

    # create dataframe of MPI_Allreduce which has the timestamp when the function was called
    allreduce_df = rank_data_df[rank_data_df['name'] == 'MPI_Allreduce']

    # drop all columns except ts
    allreduce_df = allreduce_df['ts']

    # reset the index of the dataframe
    allreduce_df = allreduce_df.reset_index(drop=True)

    allreduce_df = pd.DataFrame(allreduce_df.to_numpy(), columns=['ts'])

    return allreduce_df

@log_timed()
def cluster_collectives(df: pd.DataFrame):
    hdb = HDBSCAN(alpha=1.0, min_cluster_size=5, min_samples=5)

    hdb.fit(df.to_numpy().reshape(-1, 1))

    # create a new column in the dataframe to store the cluster labels
    df['cluster'] = hdb.labels_

    return df

@log_timed()
def define_slices(df: pd.DataFrame, total_runtime: float):
    # Initialize variables
    slices = []
    start_time = 0

    # Ensure the DataFrame is sorted by timestamp
    df = df.sort_values(by='ts')

    # Get unique clusters
    unique_clusters = df['cluster'].unique()

    # Previous end time
    previous_end_time = 0.0

    # Iterate through clusters
    for cluster in unique_clusters:
        # Get the subset of the DataFrame for the current cluster
        cluster_df = df[df['cluster'] == cluster]

        # Define the end time for the current slice
        end_time = cluster_df['ts'].max()

        if end_time > previous_end_time:
            # Append the slice to the list
            slices.append((start_time, end_time))

            # Update the start time for the next slice
            start_time = end_time

            # Update the previous end time
            previous_end_time = end_time

    # Handle the final slice
    slices.append((start_time, total_runtime))

    slices[0] = (0, slices[1][0])

    return slices