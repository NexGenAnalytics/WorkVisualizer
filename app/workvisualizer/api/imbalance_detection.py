import os
import math
import json
import multiprocessing

"""
Determine imbalance among ranks, assuming that the time slices have been found already.

Writes to files/analysis/imbalanced_slices.json, which contains a list of lists:

    [
        [rank_id, slice_id, imbalance],
        [...],
        [...],
        ...
    ]

"""

def split_events_into_slices(events, slices):
    """Split the events data into the slices."""
    num_slices = len(slices)
    rank_slices = {slice_id: [] for slice_id in range(num_slices)}
    current_slice_id = 0
    for event in events:
        current_slice = slices[current_slice_id]
        if event["ts"] > current_slice[1]:
            current_slice_id += 1
        rank_slices[current_slice_id].append(event)
    return rank_slices

def calculate_slice_stats(rank_slices):
    """Calculate stats about each slice."""
    slice_stats = {}
    for slice_id, events in rank_slices.items():
        type_counter = {"collective": 0, "mpi": 0, "kokkos": 0, "other": 0}
        type_timer = {"collective": 0.0, "mpi": 0.0, "kokkos": 0.0, "other": 0.0}
        for event in events:
            type_counter[event["type"]] += 1
            type_timer[event["type"]] += event["dur"]
        slice_stats[slice_id] = {
            "num_events": len(events),
            "type counts": type_counter,
            "type times": type_timer
        }
    return slice_stats

def find_most_imbalance(imbalanced_slices, slice_id=None, num_entries=None):

    # Isolate only requested slice
    if slice_id is not None:
        if isinstance(slice_id, int):
            imbalanced_slices = [entry for entry in imbalanced_slices if entry[1] == slice_id]
        elif isinstance(slice_id, list) or isinstance(slice_id, tuple):
            imbalanced_slices = [entry for entry in imbalanced_slices if entry[1] in slice_id]
        else:
            raise TypeError("slice_id should be an int or list of ints")

    # Sort the list by the imbalance score (3rd element in the tuple) in descending order
    imbalanced_slices.sort(key=lambda x: x[2], reverse=True)

    # Initialize ranks/slices with most imbalance
    most_imbalance = []

    # User specifies top num_entries
    if num_entries is not None:
        iter = 0
        while iter < num_entries and iter < len(imbalanced_slices):
            entry = imbalanced_slices[iter]
            most_imbalance.append(entry)
            iter += 1

    # Determine some stat for reporting
    else:
        total_imbalance = sum(entry[2] for entry in imbalanced_slices)
        mean_imbalance = total_imbalance / len(imbalanced_slices)
        var = sum((entry[2] - mean_imbalance) ** 2 for entry in imbalanced_slices) / len(imbalanced_slices)
        sigma = math.sqrt(var)

        # Look for slices greater than mean + 2*sigma
        threshold_imb = mean_imbalance + 2 * sigma
        for entry in imbalanced_slices:
            if entry[2] > mean_imbalance + 2 * sigma:
                most_imbalance.append(entry)

    return most_imbalance

def process_file(filepath, repr_slice_stats, num_slices, slices, imbalance_threshold=0.0):
    """
    Inputs:
        filepath (str):              Full path to the current events.json file
        repr_slice_stats (dict):     Contains relevant stastics for the representative rank
        num_slices (int):            Number of time slices found on the representative rank
        slices (list):               Contains tuples denoting the begin and end time of each slice
        imbalance_threshold (float): Threshold for a given rank's slice to be considered imbalanced

    This function reads in the events.json specified via `filepath` and compares each slice to the
    representative rank.

    Imbalance is calculated by: (rank_stat / repr_stat) - 1, where:
        rank_stat is the current statistic (number of events, time spent in MPI calls, etc.) for the
            specified rank and at the current slice
        repr_stat is the same statstic at the same slice, for the representative rank

    If rank_stat = repr_stat, imbalance is considered to be 0.0.

    Returns:
        imbalanced_slices (list): A list containing a list for each imbalanced slice: [rank_id, slice_id, imbalance]
    """
    # Read the JSON data
    with open(filepath) as f:
        json_data = json.load(f)

    # Get the rank ID
    rank_id = json_data[0]["rank"]

    # Process the data
    rank_slices = split_events_into_slices(json_data, slices)
    slice_stats = calculate_slice_stats(rank_slices)

    # Initialize list of imbalanced slices (will be a list of lists: [rank_id, slice_id, imbalance])
    imbalanced_slices = []

    # Compare stats to the representative rank at each slice
    for slice_id in range(num_slices):
        # Compute imbalance for total number of events
        num_events_imb = (slice_stats[slice_id]["num_events"] / repr_slice_stats[slice_id]["num_events"]) - 1

        # Compute imbalance for number of calls of each type
        type_count_imbs = {}
        for call_type, count in slice_stats[slice_id]["type counts"].items():
            type_count_imbs[call_type] = (count / repr_slice_stats[slice_id]["type counts"][call_type]) - 1

        # Compute imbalance for time spent in calls of each type
        type_time_imbs = {}
        for call_type, time in slice_stats[slice_id]["type times"].items():
            type_time_imbs[call_type] = (time / repr_slice_stats[slice_id]["type times"][call_type]) - 1

        # Aggregate for final imbalance score
        slice_imbalance = num_events_imb + sum(list(type_count_imbs.values())) + sum(list(type_time_imbs.values()))

        # Determine if the current slice is sufficiently imbalanced
        if slice_imbalance > imbalance_threshold:
            imbalanced_slices.append([rank_id, slice_id, slice_imbalance])

    return imbalanced_slices

def analyze_slices(events_dir: str, rank: int, slices: list, imbalance_threshold=3.0):
    """Find ranks with imbalanced slices, assuming that each events file is sorted by start time."""
    # First, separate the representative rank from the rest
    repr_filename = ""
    other_filenames = []
    for events_file in os.listdir(events_dir):
        if f"events-{rank}" in events_file:
            repr_filename = events_file
        else:
            other_filenames.append(events_file)

    # Then get the stats for the representative rank
    with open(os.path.join(events_dir, repr_filename)) as r:
        repr_json_data = json.load(r)
    repr_rank_slices = split_events_into_slices(repr_json_data, slices)
    repr_slice_stats = calculate_slice_stats(repr_rank_slices)

    # Then determine the number of slices and define the imbalance threshold
    num_slices = len(slices)

    # Loop through all ranks' events files with multiprocessing
    with multiprocessing.Pool() as pool:
        results = pool.starmap(
            process_file,
            [(os.path.join(events_dir, filename), repr_slice_stats, num_slices, slices, imbalance_threshold) for filename in other_filenames]
        )

    # Combine results from all processes and sort by slice
    imbalanced_slices = []
    for result in results:
        imbalanced_slices.extend(result)
    imbalanced_slices.sort(key=lambda x: x[1], reverse=True)

    return imbalanced_slices

def main():
    # Define slices and representative rank
    representative_slices = [(0.0, 0.21), (0.21, 0.41), (0.41, 0.64), (0.64, 0.86), (0.86, 1.11), (1.35, 1.5)]
    representative_rank = 35

    # Identify events directory
    files_dir = os.path.join(os.getcwd(), "files")
    events_dir = os.path.join(files_dir, "events")

    # Find all imbalanced slices (slices with imbalance greater than imb_threshold)
    imb_threshold = 3.0
    imbalanced_slices = analyze_slices(events_dir, representative_rank, representative_slices, imbalance_threshold=imb_threshold)

    # Isolate only the most imbalanced slices
    most_imbalanced_slices = find_most_imbalance(imbalanced_slices)

    # Create the analysis dir (if it doesn't exist)
    analysis_dir = os.path.join(files_dir, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)

    # Write results to imbalanced_slices.json
    with open(os.path.join(analysis_dir, "imbalanced_slices.json"), "w") as json_file:
        json.dump(most_imbalanced_slices, json_file, indent=4)

if __name__ == "__main__":
    main()
