import os
import math
import json
import multiprocessing

"""
Determine time lost among ranks and slices.

Output:

    files/analysis/time_lost_ranks.json: contains rank-specific statistics:

        - rank: the rank ID
        - slice: the slice ID
        - time_lost: Time spent in Allreduce (for that slice, on that rank) minus the same stat for the representative rank
        - num_events: Total number of function calls that occurred in that slice
        - type_counts: Total number of function calls of each type that occurred in that slice
        - type_times: Total time spent in each function type in that slice
        - <pct_diffs>: For num_events, type_counts, and type_times, we calculate the percent difference wrt the representative rank
            - A negative pct diff means that the specified rank had fewer counts or less time than the representative rank
        - total_pct_diff: Sum of all percent differences found

    files/analysis/time_lost.json: contains only the total time lost per slice:
        - Map of slice id to aggregated time lost (found by summing the time_lost for each rank in that slice)
"""

def split_events_into_slices(events, slices):
    """Split the events data into the slices."""
    # slice_ids = list(slices.keys())
    slice_ids = list(range(len(slices)))
    rank_slices = {slice_id: [] for slice_id in slice_ids}
    slice_id_iterator = 0
    for event in events:
        current_slice_id = slice_ids[slice_id_iterator]
        current_slice = slices[current_slice_id]
        if event["ts"] > current_slice[1]:
            slice_id_iterator += 1
        rank_slices[current_slice_id].append(event)
    return rank_slices

def calculate_slice_stats(rank_slices):
    """Calculate stats about each slice."""
    slice_stats = {}
    for slice_id, events in rank_slices.items():
        type_counter = {"mpi_collective": 0, "mpi_p2p": 0, "kokkos": 0, "other": 0}
        type_timer = {"mpi_collective": 0.0, "mpi_p2p": 0.0, "kokkos": 0.0, "other": 0.0, "MPI_Allreduce": 0.0}
        for event in events:
            type_counter[event["type"]] += 1
            type_timer[event["type"]] += event["dur"]
            if event["name"] == "MPI_Allreduce":
                type_timer["MPI_Allreduce"] += event["dur"]
        slice_stats[slice_id] = {
            "num_events": len(events),
            "type counts": type_counter,
            "type times": type_timer
        }
    return slice_stats

def sort_rank_slices_by_time_lost(all_slices, slice_id=None, num_entries=None):

    # Isolate only requested slice
    if slice_id is not None:
        if isinstance(slice_id, int):
            all_slices = [entry for entry in all_slices if entry["slice"] == slice_id]
        elif isinstance(slice_id, list) or isinstance(slice_id, tuple):
            all_slices = [entry for entry in all_slices if entry["slice"] in slice_id]
        else:
            raise TypeError("slice_id should be an int or list of ints")

    # Sort the list by the time lost (in descending order)
    all_slices.sort(key=lambda x: x["time_lost"], reverse=True)

    # Initialize ranks/slices with most time lost
    # most_time_lost = {}

    # User specifies top num_entries
    # if num_entries is not None:
    #     iter = 0
    #     while iter < num_entries and iter < len(all_slices):
    #         entry = all_slices[iter]
    #         slice_id = entry["slice"]
    #         if slice_id not in most_time_lost:
    #             most_time_lost[slice_id] = []
    #         most_time_lost[slice_id].append(entry)
    #         iter += 1

    # # Determine some stat for reporting
    # else:
    #     total_time_lost = sum(entry["time_lost"] for entry in all_slices)
    #     mean_time_lost = total_time_lost / len(all_slices)
    #     var = sum((entry["time_lost"] - mean_time_lost) ** 2 for entry in all_slices) / len(all_slices)
    #     sigma = math.sqrt(var)

    #     # Look for slices greater than mean + 2*sigma
    #     threshold_time_lost = mean_time_lost + 2 * sigma
    #     for entry in all_slices:
    #         if entry["time_lost"] > threshold_time_lost:
    #             slice_id = entry["slice"]
    #             if slice_id not in most_time_lost:
    #                 most_time_lost[slice_id] = []
    #             most_time_lost[slice_id].append(entry)

    return all_slices

def find_time_losing_slices(all_slices):
    """Aggregates across all ranks to get the total time lost for each slice."""
    total_time_lost_per_slice = {}
    for entry in all_slices:
        slice_id = entry['slice']
        if slice_id not in total_time_lost_per_slice:
            total_time_lost_per_slice[slice_id] = entry['time_lost']
        else:
            total_time_lost_per_slice[slice_id] += entry['time_lost']
    return total_time_lost_per_slice

def process_file(filepath, repr_slice_stats, num_slices, slices):
    """
    Inputs:
        filepath (str):          Full path to the current events.json file
        repr_slice_stats (dict): Contains relevant stastics for the representative rank
        num_slices (int):        Number of time slices found on the representative rank
        slices (dict):           Maps slice ids to tuples denoting the begin and end time of that slice

    This function reads in the events.json specified via `filepath` and compares each slice to the
    representative rank.

    Time lost is calculated by the amount of time a rank spends in MPI_Allreduce (compared to the representative rank)

    Returns:
        time_losing_slices (list): A list containing a list for each time-losing slice: [rank_id, slice_id, stats_dict]
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
    rank_slice_data = []

    # slice_ids = list(slices.keys())
    slice_ids = list(range(len(slices)))

    # Compare stats to the representative rank at each slice
    for slice_id in slice_ids:

        # First, calculate the time lost in Allreduce functions
        time_lost = repr_slice_stats[slice_id]["type times"]["mpi_collective"] - slice_stats[slice_id]["type times"]["mpi_collective"]

        # Compute percent difference for total number of events
        repr_num_events = repr_slice_stats[slice_id]["num_events"]
        if repr_num_events == 0:
            num_events_pct_diff = 0.0
        else:
            num_events_pct_diff = (slice_stats[slice_id]["num_events"] / repr_slice_stats[slice_id]["num_events"]) - 1

        # Compute percent difference for number of calls of each type
        type_counts_pct_diffs = {}
        for call_type, count in slice_stats[slice_id]["type counts"].items():
            repr_counts = repr_slice_stats[slice_id]["type counts"][call_type]
            if repr_counts == 0:
                type_counts_pct_diffs[call_type] = 0.0
            else:
                type_counts_pct_diffs[call_type] = (count / repr_counts) - 1

        # Compute percent difference for time spent in calls of each type
        type_times_pct_diffs = {}
        for call_type, time in slice_stats[slice_id]["type times"].items():
            repr_times = repr_slice_stats[slice_id]["type times"][call_type]
            if repr_times == 0:
                type_times_pct_diffs[call_type] = 0.0
            else:
                type_times_pct_diffs[call_type] = (time / repr_times) - 1

        # Aggregate for final difference score
        total_pct_diff = num_events_pct_diff + sum(list(type_counts_pct_diffs.values())) + sum(list(type_times_pct_diffs.values()))

        # Create a final stats dict for each slice
        rank_slice_dict = {
            "rank": rank_id,
            "slice": slice_id,
            "time_lost": time_lost,
            "num_events": slice_stats[slice_id]["num_events"],
            "num_events_pct_diff": num_events_pct_diff,
            "type_counts": slice_stats[slice_id]["type counts"],
            "type_counts_pct_diffs": type_counts_pct_diffs,
            "type_times": slice_stats[slice_id]["type times"],
            "type_times_pct_diffs": type_times_pct_diffs,
            "total_pct_diff": total_pct_diff
        }

        rank_slice_data.append(rank_slice_dict)

    return rank_slice_data

def analyze_slices(events_dir: str, rank: int, slices: list):
    """Find statistics per rank per slice, assuming that each events file is sorted by start time."""
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
            [(os.path.join(events_dir, filename), repr_slice_stats, num_slices, slices) for filename in other_filenames]
        )

    # Combine results from all processes and sort by slice
    all_slices_stats = []
    for result in results:
        all_slices_stats.extend(result)
    all_slices_stats.sort(key=lambda x: x["slice"], reverse=True)

    return all_slices_stats

def run_slice_analysis(files_dir, representative_rank, representative_slices):
    # Specify the events directory
    events_dir = os.path.join(files_dir, "events")

    # Find all statistics for all slices
    all_slices = analyze_slices(events_dir, representative_rank, representative_slices)

    # Isolate ranks that lose time
    time_losing_rank_slices = sort_rank_slices_by_time_lost(all_slices, num_entries=1)

    # Aggregate across all ranks to find time-losing slices
    time_losing_slices = find_time_losing_slices(all_slices)

    # Create the analysis dir (if it doesn't exist)
    analysis_dir = os.path.join(files_dir, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)

    # Write out the data for all ranks
    with open(os.path.join(analysis_dir, "all_ranks_analyzed.json"), "w") as all_ranks_json:
        json.dump(all_slices, all_ranks_json, indent=4)

    # Write out the data for time-losing ranks
    with open(os.path.join(analysis_dir, "time_lost_ranks.json"), "w") as ranks_json:
        json.dump(time_losing_rank_slices, ranks_json, indent=4)

    # Write results for time-losing slices
    with open(os.path.join(analysis_dir, "time_lost.json"), "w") as slices_json:
        json.dump(time_losing_slices, slices_json, indent=4)

    return time_losing_rank_slices, time_losing_slices

def main():
    # Define slices and representative rank
    representative_slices = [(0, 0.01178184), (0.01178184, 0.34445776100000003), (0.34445776100000003, 0.923146926), (0.923146926, 1.5214891480000001), (1.5214891480000001, 2.130170211), (2.130170211, 2.730077892), (2.730077892, 3.106437574), (3.106437574, 3.106765707)]

    representative_rank = 0

    # Identify events directory
    files_dir = os.path.join(os.getcwd(), "files")

    # Run the analysis
    run_slice_analysis(files_dir, representative_rank, representative_slices)

if __name__ == "__main__":
    main()
