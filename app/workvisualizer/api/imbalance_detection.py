import os
import json
import multiprocessing

"""Determine imbalance among ranks, assuming that the time slices have been found already."""

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

def process_file(filepath, repr_slice_stats, num_slices, slices, imbalance_threshold):
    # Read the JSON data
    with open(filepath) as f:
        json_data = json.load(f)

    # Get the rank ID
    rank_id = json_data[0]["rank"]

    # Process the data
    rank_slices = split_events_into_slices(json_data, slices)
    slice_stats = calculate_slice_stats(rank_slices)

    imbalanced_slices = {slice_id: [] for slice_id in range(num_slices)}

    # Compare stats to the representative rank at each slice
    for slice_id in range(num_slices):
        # Compute imbalances for each slice
        num_events_imb = (slice_stats[slice_id]["num_events"] / repr_slice_stats[slice_id]["num_events"]) - 1

        type_count_imbs = {}
        for call_type, count in slice_stats[slice_id]["type counts"].items():
            type_count_imbs[call_type] = (count / repr_slice_stats[slice_id]["type counts"][call_type]) - 1

        type_time_imbs = {}
        for call_type, time in slice_stats[slice_id]["type times"].items():
            type_time_imbs[call_type] = (time / repr_slice_stats[slice_id]["type times"][call_type]) - 1

        # Aggregate for final imbalance score
        slice_imbalance = num_events_imb + sum(list(type_count_imbs.values())) + sum(list(type_time_imbs.values()))

        # Determine if the current slice is sufficiently imbalanced
        if slice_imbalance > imbalance_threshold:
            imbalanced_slices[slice_id].append({rank_id: slice_imbalance})

    return imbalanced_slices

def analyze_slices(events_dir: str, rank: int, slices: list):
    """Find ranks with imbalanced slices, assuming that the events file is sorted by start time."""
    # First, get the stats for the representative rank
    repr_filepath = [events_file for events_file in os.listdir(events_dir) if f"events-{rank}" in events_file][0]
    with open(os.path.join(events_dir, repr_filepath)) as r:
        repr_json_data = json.load(r)
    repr_rank_slices = split_events_into_slices(repr_json_data, slices)
    repr_slice_stats = calculate_slice_stats(repr_rank_slices)

    # Then determine the number of slices and define the imbalance threshold
    num_slices = len(slices)
    imbalance_threshold = 3.0

    # Loop through all ranks' events files with multiprocessing
    with multiprocessing.Pool() as pool:
        results = pool.starmap(
            process_file,
            [(os.path.join(events_dir, filename), repr_slice_stats, num_slices, slices, imbalance_threshold) for filename in os.listdir(events_dir)]
        )

    # Combine results from all processes
    imbalanced_slices = {slice_id: [] for slice_id in range(num_slices)}
    for result in results:
        for slice_id, imbalances in result.items():
            imbalanced_slices[slice_id].extend(imbalances)

    # Output a summary of the imbalance
    print("\n------------ Imbalance Summary ------------")
    for slice_id in range(num_slices):
        print(f"\n --- Slice {slice_id}")
        print(imbalanced_slices[slice_id])

    return imbalanced_slices

def main():
    # Define slices and representative rank
    representative_slices = [(0.0, 0.21), (0.21, 0.41), (0.41, 0.64), (0.64, 0.86), (0.86, 1.11), (1.35, 1.5)]
    representative_rank = 35

    # Identify events directory
    files_dir = os.path.join(os.getcwd(), "files")
    events_dir = os.path.join(files_dir, "events")

    # Call the analyze function
    imbalanced_slices = analyze_slices(events_dir, representative_rank, representative_slices)

main()
