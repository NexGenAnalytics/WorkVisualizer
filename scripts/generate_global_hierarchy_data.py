import os
import json
import argparse


"""
Takes in the hierarchical JSON (from generate_full_hierarchy_data.py) and creates a GLOBAL hierarchy (ie combining the same event into a single slice).
The resulting JSON can be used to create the spacetime plots.
"""


######################################################################################################################
#################                                                                                    #################
#################                                       SET UP                                       #################
#################                                                                                    #################
######################################################################################################################


def merge_children(event):
    if "children" in event:
        # Merge children first
        event["children"] = merge_and_process(event["children"])
        for child in event["children"]:
            merge_children(child)
    return event

def merge_and_process(children_list):
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
        merged_list.append(value)

    return merged_list

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
    output_dir = os.path.join(current_dir, "data", "d3_hierarchy")
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
    output_path = f"{output_dir}/{app_abr}_{rank}r_{n_steps}s_global_hierarchy.json"
else:
    output_path = os.path.join(output_dir, args.output_filename)


# Read in all data
trace_json_filepath = os.path.join(current_dir, json_file)
f = open(trace_json_filepath)
json_data = json.load(f)

# Merge all children events
global_data = merge_children(json_data)

# Now write out the json
with open(output_path, "w") as out_json:
    json.dump(json_data, out_json)
