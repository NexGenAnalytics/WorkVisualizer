import os
import json
import pandas as pd
import argparse
import numpy as np
from collections import defaultdict
from math import isclose
from scipy.stats import mode
from scipy.signal import find_peaks
from scipy.fft import fft, fftshift
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib import colormaps


"""
Takes in the hierarchical JSON (from generate_hierarchy_data.py) and creates a GLOBAL hierarchy (ie combining the same event into a single slice).
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

def merge_children(event):
    if "children" in event:
        # Merge children first
        event["children"] = merge_and_process(event["children"])
        for child in event["children"]:
            merge_children(child)
    return event

def merge_and_process(children_list):
    # merged_dict = defaultdict(lambda: {"name": "", "duration": 0, "count": 0, "children": []})
    merged_dict = {}

    for child in children_list:
        name = child["name"]
        if name not in merged_dict:
            merged_dict[name] = child
            merged_dict[name]["count"] = 1
        else:
            merged_dict[name]["count"] += 1

        if "children" in child:
            merged_dict[name]["children"].extend(child["children"])
        else:
            merged_dict[name]["duration"] += child["duration"]
    
    # Create the merged list and calculate average duration if necessary
    merged_list = []
    for value in merged_dict.values():
        # if value["count"] > 1:
        #     value["average duration"] = value["duration"] / value["count"]
        # else:
        #     value.pop("count")
        merged_list.append(value)
    
    return merged_list

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
output_dir = os.path.join(current_dir, "data", "d3_hierarchy")
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

# Merge all children events
global_data = merge_children(json_data)
# print(json_data)

# Now write out the json
output_path = f"{output_dir}/{app_abr}_{rank}r_{n_steps}s_global_hierarchy.json"
with open(output_path, "w") as out_json:
    json.dump(json_data, out_json)


######################################################################################################################
#################                                                                                    #################
#################                                 GENERATE TIME PLOT                                 #################
#################                                                                                    #################
######################################################################################################################
