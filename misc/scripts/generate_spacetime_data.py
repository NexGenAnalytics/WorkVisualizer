import os
import json
import argparse


"""
Takes in the hierarchical JSON (from generate_hierarchy_data.py) and flattens it into a list of events.
The resulting JSON can be used to create the spacetime plots.
"""

######################################################################################################################
#################                                                                                    #################
#################                                       SET UP                                       #################
#################                                                                                    #################
######################################################################################################################

def sort_functions(event_dict):
    path = event_dict["path"]
    if path == "":
        return 0
    elif path.count("/") == 0:
        return 1
    else:
        return path.count("/") + 1

def flatten_events(event_dict):
    total_flattened_list = []
    if "children" in event_dict:
        children_list = event_dict["children"]
        for event in children_list:
            total_flattened_list.extend(flatten_events(event))
    else:
        total_flattened_list.append(event_dict)

    return total_flattened_list

# Parse command line arg for the json file
parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
parser.add_argument("-od", "--output_dir", default="", help="Path to the output file")
parser.add_argument("-of", "--output_filename", default="", help="Name of the output file")

# Read in all arguments
args = parser.parse_args()
json_file = args.input

# Create save directory
current_dir = os.getcwd()
if args.output_dir == "":
    output_dir = os.path.join(current_dir, "data", "d3_scatter")
else:
    output_dir = args.output_dir
os.makedirs(output_dir, exist_ok=True)

# Get problem info
if args.output_filename == "":
    file_splits = json_file.split("_")
    app_abr = file_splits[0].lower()
    if "/" in app_abr:
        app_abr = app_abr.split("/")[-1]
    if app_abr == "mpm" or app_abr == "exampm":
        app = "ExaMPM"
    elif app_abr == "md" or app_abr == "examinimd":
        app = "ExaMiniMD"
    elif app_abr == "em" or app_abr == "miniem":
        app = "MiniEM"
    else:
        app = app_abr
    rank = int(file_splits[1].split("r")[0]) if "r_" in json_file else 0
    n_steps = int(file_splits[2].split("s")[0])
    output_path = f"{output_dir}/{app_abr}_{rank}r_{n_steps}s_pruned_scatter.json"
else:
    output_path = os.path.join(output_dir, args.output_filename)


# Create list of all MPI collective functions for reference if needed
all_collectives = ["MPI_Allgather", "MPI_Allgatherv", "MPI_Allreduce", "MPI_Alltoall",
                   "MPI_Alltoallv", "MPI_Alltoallw", "MPI_Barrier", "MPI_Bcast",
                   "MPI_Gather", "MPI_Gatherv", "MPI_Iallgather", "MPI_Iallreduce",
                   "MPI_Ibarrier", "MPI_Ibcast", "MPI_Igather", "MPI_Igatherv",
                   "MPI_Ireduce", "MPI_Iscatter", "MPI_Iscatterv", "MPI_Reduce",
                   "MPI_Scatter", "MPI_Scatterv", "MPI_Exscan", "MPI_Op_create",
                   "MPI_Op_free", "MPI_Reduce_local", "MPI_Reduce_scatter", "MPI_Scan",
                   "MPI_User_function"]

# Read in all data
trace_json_filepath = os.path.join(current_dir, json_file)
f = open(trace_json_filepath)
json_data = json.load(f)

# Flatten the hierarchical dict
flattened_events = flatten_events(json_data)

# Determine the increments (likely want to do this in JavaScript)
increment = 1.0 / len(flattened_events)

# Initialize known functions
known_increments = {}

# Sort the JSON by path
sorted_events = sorted(flattened_events, reverse=True, key=sort_functions)

# Then create a json with the relevant info
iter = 1
for event in sorted_events:

    # First, we can remove the "children" object now
    if "children" in event:
        del event["children"]

    # Then we want to make sure the duration is in the event
    if "duration" not in event:
        event["duration"] = event["end_time"] - event["begin_time"]

    # Then determine the type of the call
    if event["name"] in all_collectives:
        call_type = "collective"
    elif "MPI_" in event["name"]:
        call_type = "mpi"
    else:
        call_type = "kokkos"
    event["type"] = call_type

    # Then we need to determine the y value for this function

    # Create a temporary name that includes the path
    tmp_name = event["name"] + event["path"]

    # Determine the increment of the function
    if tmp_name in known_increments:
        y_val = known_increments[tmp_name]
    else:
        y_val = iter * increment
        known_increments[tmp_name] = y_val
        iter += 1

    # Add to the event
    event["y_value"] = y_val

# Now write out the json
with open(output_path, "w") as out_json:
    json.dump(sorted_events, out_json)
