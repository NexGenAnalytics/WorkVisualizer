import os
import json
import pandas as pd
import argparse
import numpy as np
from math import isclose
from scipy.stats import mode
from scipy.signal import find_peaks
from scipy.fft import fft, fftshift
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib import colormaps


"""
Takes in the hierarchical JSON (from generate_hierarchy_data.py) and flattens it into a list of events.
The resulting JSON can be used to create the spacetime plots.
"""


######################################################################################################################
#################                                                                                    #################
#################                                       SET UP                                       #################
#################                                                                                    #################
######################################################################################################################

# Set time constraint based on requested metaslice
def time_constraint(begin_time, metaslice):
    if metaslice == "init":
        return 0 < begin_time < 10
    elif metaslice == "iter":
        return 15.20 < begin_time < 15.50
    elif metaslice == "loop":
        return 10 < begin_time < 39
    elif metaslice == "final":
        return begin_time > 39
    else:
        return begin_time > 0

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
parser.add_argument("-s", "--save", action="store_true", help="Whether or not to save the plot to a file.")
parser.add_argument("-a", "--all", action="store_true", help="Whether or not to plot ALL functions on the final plot (and not just the periodic ones).")
parser.add_argument("-f", "--filtered", action="store_true", help="Plots only the FILTERED functions on the final plot.")
parser.add_argument("-sort", "--sorting_key", default=None, help="`path`, `call`, or `rank`")
parser.add_argument("-dt", "--draw_timesteps", action="store_true", help="Whether or not to draw the timesteps on the final plot.")
parser.add_argument("-dm", "--draw_macroloops", action="store_true", help="Whether or not to draw the macroloopss on the final plot.")
parser.add_argument("-p", "--proc", default=-1, help="Processor to be plotted. Defaults to all available processors.")
parser.add_argument("-t", "--target", default=0, help="Processor to be colored in (when all procs are plotted). Defaults to first processor.")
parser.add_argument("-b", "--bin_count", default=1000000, help="Number of timesteps into which to bin the full application duration for frequency analysis.")
parser.add_argument("-m", "--metaslice", default="all", help="init, loop, final, or all")
parser.add_argument("-v", "--vertical", action="store_true", help="Plots the calls over time plot vertically (to sync visually with the calltree).")

# Read in all arguments
args = parser.parse_args()
json_file = args.input
save = args.save
num_bins = int(args.bin_count)
draw_timesteps = args.draw_timesteps
draw_macroloops = args.draw_macroloops
output_proc = int(args.proc)
plot_all_functions = args.all
plot_filtered_functions = args.filtered
target_proc = int(args.target)
metaslice = args.metaslice
vertical_plot = args.vertical

# Get problem info
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


# Create save directory
current_dir = os.getcwd()
output_dir = os.path.join(current_dir, "data", "d3_scatter")
os.makedirs(output_dir, exist_ok=True)

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

# Determine the increments
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
output_path = f"{output_dir}/{app_abr}_{rank}r_{n_steps}s_pruned_scatter.json"
with open(output_path, "w") as out_json:
    json.dump(sorted_events, out_json)


######################################################################################################################
#################                                                                                    #################
#################                                 GENERATE TIME PLOT                                 #################
#################                                                                                    #################
######################################################################################################################
