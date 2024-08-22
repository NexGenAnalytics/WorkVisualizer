"""Aggregates data from each processor's metadata files into a single, global metadata file."""
import os
import json
# imoprt numpy as np

def read_in_proc_metadata_files(files_dir):
    metadata_proc_dir = os.path.join(files_dir, "metadata", "procs")
    all_metadata_files = [os.path.join(metadata_proc_dir, metadata_file) for metadata_file in os.listdir(metadata_proc_dir)]
    return all_metadata_files

def aggregate_all_proc_metadata(list_of_proc_metadata_files):
    # Initalize useful variables to loop over
    global_keys = ["cali.caliper.version", "mpi.world.size", "cali.channel"]
    calltypes = ["kokkos", "mpi_p2p", "mpi_collective", "other"]

    # Initalize the global data
    global_metadata = {}
    global_known_ranks = []
    global_known_depths = []
    global_average_counts = {}
    global_unique_counts = {calltype: 0 for calltype in calltypes}
    global_total_counts = {calltype: 0 for calltype in calltypes}
    tmp_global_biggest_calls = {}
    global_biggest_calls = {}
    global_start = 100.
    global_end = 0.
    global_runtime = 0.

    known_ftn_ids = []

    first_file = True

    for proc_metadata_file in list_of_proc_metadata_files:
        # Read in the current file
        with open(proc_metadata_file) as f:
            proc_metadata = json.load(f)

        # Start with all the constant metadata from a single file
        if first_file:
            first_file = False
            for key in global_keys:
                global_metadata[key] = proc_metadata[key]

        # Add all known ranks and depths
        for rank in proc_metadata["known.ranks"]:
            if rank not in global_known_ranks:
                global_known_ranks.append(rank)
        for depth in proc_metadata["known.depths"]:
            if depth not in global_known_depths:
                global_known_depths.append(depth)

        # Update start and end times
        if proc_metadata["program.start"] < global_start:
            global_start = proc_metadata["program.start"]
        if proc_metadata["program.end"] > global_end:
            global_end = proc_metadata["program.end"]

        # Update global counts
        for key_rank, counts_dict in proc_metadata["total.counts"].items():
            for calltype in calltypes:
                global_total_counts[calltype] += counts_dict[calltype]

        # Update unique counts
        for ftn_id, ftn_type in proc_metadata["unique.ftnids"].items():
            if ftn_id not in known_ftn_ids:
                global_unique_counts[ftn_type] += 1
                known_ftn_ids.append(ftn_id)

        # Update biggest calls
        for big_call in proc_metadata["biggest.calls"]:
            ftn_name = big_call["name"]
            num_ranks = len(big_call["rank_info"])
            if ftn_name not in tmp_global_biggest_calls:
                tmp_global_biggest_calls[ftn_name] = {"n_ranks": num_ranks, "dur": big_call["dur"]}
            else:
                tmp_global_biggest_calls[ftn_name]["n_ranks"] += num_ranks
                tmp_global_biggest_calls[ftn_name]["dur"] += big_call["dur"]


    # Update known ranks and depths
    global_metadata["known.ranks"] = global_known_ranks
    global_metadata["known.depths"] = global_known_depths

    # Add aggregated values
    global_metadata["maximum.depth"] = max(global_known_depths)
    global_metadata["program.start"] = global_start
    global_metadata["program.end"] = global_end
    global_metadata["program.runtime"] = global_end - global_start

    # Find the biggest calls
    for ftn_name, big_call in tmp_global_biggest_calls.items():
        global_biggest_calls[ftn_name] = big_call["dur"] / big_call["n_ranks"]
    global_metadata["biggest.calls"] = global_biggest_calls

    # Get average counts per rank
    for calltype in calltypes:
        global_average_counts[calltype] = global_total_counts[calltype] / len(global_known_ranks)

    # Write out global counts
    global_metadata["total.counts"] = global_total_counts
    global_metadata["unique.counts"] = global_unique_counts
    global_metadata["average.counts"] = global_average_counts

    # Return the global metadata
    return global_metadata

def write_out_global_metadata(data, files_dir, depth_string, indent=0):
    metadata_dir = os.path.join(files_dir, "metadata")
    metadata_file = os.path.join(metadata_dir, f"metadata-{depth_string}.json")

    with open(metadata_file, "w") as global_metadata_output:
        json.dump(data, global_metadata_output, indent=indent)

def aggregate_metadata(files_dir):
    print("CALLING AGGREGATE METADATA")
    proc_metadata_files = read_in_proc_metadata_files(files_dir)
    global_metadata = aggregate_all_proc_metadata(proc_metadata_files)

    depth_level = proc_metadata_files[0].split("depth_")[1].split(".")[0]
    depth_str = f"depth_{depth_level}"
    write_out_global_metadata(global_metadata, files_dir, depth_str, 4)

