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
            merged_dict[name]["dur"] += child["dur"]

    # Create the merged list and calculate average duration if necessary
    merged_list = []
    for value in merged_dict.values():
        merged_list.append(value)

    return merged_list

def hierarchy_to_global_hierarchy(input_file, output_file):

    # Read in all data
    f = open(input_file)
    json_data = json.load(f)

    # Merge all children events
    global_data = merge_children(json_data)

    # Now write out the json
    with open(output_file, "w") as out_json:
        json.dump(global_data, out_json, indent=1)
