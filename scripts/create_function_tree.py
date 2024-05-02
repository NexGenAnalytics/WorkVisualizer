"""Plots the MPI and Kokkos data over time."""


import os
import json
import argparse
import numpy as np


"""
Takes in a trace json and outputs the frequency of a given call.

Steps to recreate:
  - export KOKKOS_TOOLS_LIBS=/path/to/libcaliper.so
  - export CALI_CONFIG_FILE=/path/to/caliper.config
  - <run program>
        - MiniEM:    mpirun -n 4 ./PanzerMiniEM_BlockPrec.exe --numTimeSteps=10
        - ExaMiniMD: mpirun -np 4 -bind-to socket ./ExaMiniMD -il ../input/in.lj --comm-type MPI --kokkos-map-device-id-by=mpi_rank
        - ExaMPM:    mpirun -n 4 ./DamBreak 0.05 2 0 0.1 1.0 10 serial
  - cali-query -q "SELECT * FORMAT json" alltrace-<rank>.cali | tee <filename>.json
        - <filename> Formatting: <app>_<rank>r_<num_steps>s_<misc>.json)
        - Example: em_0r_100s_kokkostrace.json
  - mv <filename> ${WORKVIZ_DIR}/data
"""


######################################################################################################################
#################                                                                                    #################
#################                                       SET UP                                       #################
#################                                                                                    #################
######################################################################################################################

def custom_sort_key(event):
    if "kernel_type" in event:
        return len(event["kernel_type"].split("/"))
    return np.inf

def get_children_dict_index(current_list):
    if current_list is not None:
        for i in range(len(current_list)):
            elt = current_list[i]
            if isinstance(elt, dict) and "children" in elt:
                return i
    return None

def get_children_list(current_list, region_name):
    for elt in current_list:
        if isinstance(elt, dict) and "children" in elt and elt["name"] == region_name:
            return elt["children"]

# Parse command line arg for the json file
parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
parser.add_argument("-s", "--save", action="store_true", help="Whether or not to save the plot to a file.")
parser.add_argument("-e", "--expected", default=None, help="The expected frequency of a given dataset (i.e. the value that should be found by the WV.)")
parser.add_argument("-p", "--proc", default=-1, help="Processor to be plotted. Defaults to all available processors.")
parser.add_argument("-t", "--target", default=0, help="Processor to be colored in (when all procs are plotted). Defaults to first processor.")
parser.add_argument("-o", "--order", action="store_true", help="Whether or not to sort the functions in the resulting plots.")
parser.add_argument("-b", "--bin_count", default=1000, help="Number of timesteps into which to bin the full application duration for frequency analysis.")

# Read in all arguments
args = parser.parse_args()
json_file = args.input
save = args.save
expected_freq = args.expected
num_bins = int(args.bin_count)
output_proc = int(args.proc)
order = args.order
target_proc = int(args.target)

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
elif app_abr == "testdata" or app_abr == "testapp":
    app = "Test App"
else:
    app = app_abr
n_procs = int(file_splits[1].split("p")[0])
n_steps = int(file_splits[2].split("s")[0])
call_type = "MPI" if "mpi" in file_splits[3].lower() else "All"


# Read in all calls
current_dir = os.getcwd()
trace_json_filepath = os.path.join(current_dir, json_file)
f = open(trace_json_filepath)
json_data = json.load(f)
json_data = sorted(json_data, key=custom_sort_key)

# Initialize all timings
hierarchies = {"name": "main",
               "children": []}

known_events = {}

# Loop through all events to isolate relevant calls
for event in json_data:

    # Only look at event.begin entries
    if "event.begin#region" in event or "event.begin#mpi.function" in event:

        if event["mpi.rank"] != 0:
            continue

        # Get the function name (note: this can be an MPI call, a Kokkos call, or a new Kokkos region)
        function_name = event["event.begin#region"] if "event.begin#region" in event else event["event.begin#mpi.function"]

        if "Kokkos" in function_name or "Tpetra" in function_name:
            continue

        # Determine if the event is creating a new region
        new_region = False
        if "kernel_type" in event:
            region_id = event["kernel_type"].count("kokkos.user_region")

            # New region-creating events end with "kokkos.user_region" (as opposed to kokkos.parallel_for or kokkos.fence)
            # Since MPI calls don't end in any kokkos kernel, they'll always end with user_region (so ignore them in this context)
            if event["kernel_type"].endswith("kokkos.user_region") and "MPI" not in function_name:
                new_region = True
        else:
            region_id = 0

        # Increment the region_id of all non-region-making functions
        if not new_region:
            region_id += 1

        # Add the region id to the known_events dict, if not already there
        if region_id not in known_events:
            known_events[region_id] = []

        # Make sure the function doesn't currently exist at the region id
        if function_name in known_events[region_id]:
            continue

        if "CG" in function_name:
            print(f"Processing {function_name}")

        # Then update the known_regions dict so we don't repeat regions
        known_events[region_id].append(function_name)

        # Set the current list to the top level (region 0)
        current_list = hierarchies["children"]

        # Now update the current_list until we are in the correct region, then append to that region's "children" dict
        for current_region in range(region_id):

            # Create the new region
            if new_region:

                # Make sure that we're at the correct level
                if current_region == region_id - 1:

                    # Then add the children dict into the current list and move down a level
                    dict_idx = get_children_dict_index(current_list)

                    # If there is already a dict, rename it to this region (this is the case where we made the region without knowing the name)
                    if dict_idx and current_list[dict_idx]["name"] == "stand-in":
                            current_list[dict_idx]["name"] = function_name
                            print(f"Rewrote region for {function_name}.")
                    else:
                        current_list.append({"name": function_name, "children": []})
                    current_list = get_children_list(current_list, function_name)

                # Otherwise, update the current list to the next level and try again
                else:
                    current_list = get_children_list(current_list)

            # If we're not creating a new region, this must be a function (MPI or Kokkos)
            else:

                # Make sure we're in the correct region, then append
                if current_region == region_id - 1:
                    current_list.append({"name": function_name, "value": 0.0})

                # Update the current list to the next level and try again
                elif get_children_dict_index(current_list) is not None:
                    current_list = get_children_list(current_list)

                # Create the dict with a dummy "name" that will be overwritten later once we know it
                else:
                    current_list.append({"name": "stand-in", "children": []})
                    current_list = get_children_list(current_list)

print(hierarchies)

output_dir = os.path.join(current_dir, "hierarchies", app)
os.makedirs(output_dir, exist_ok=True)

output_path = f"{output_dir}/{app_abr}_{n_procs}p_{n_steps}s_d3_hierarchy.json"

with open(output_path, "w") as out_json:
    json.dump(hierarchies, out_json)
