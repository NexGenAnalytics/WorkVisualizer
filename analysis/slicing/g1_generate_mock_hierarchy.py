import os
import json
import random

"""
This script generates a mock hierarchy, where the "name" provided would correspond,
eventually, to the ftn_id of a specific event. The goal is to identify that there are
three metaslices (initialization, solving, and finalization), where the solving loop
is broken into num_loops (for now, 5) iterations.
"""

# Initialize root node
root_node = {"name": "0", "children": []}

# Start with an initialization phase
initialization = [
    {"name": "1",
     "children": [
        {"name": "2"},
        {"name": "3"}
     ]},
    {"name": "4",
     "children": [
        {"name": "5"}
     ]}
]

# Determine graph of a single loop
single_loop = [
    {"name": "6",
     "children": [
        {"name": "7"},
        {"name": "8"},
        {"name": "9",
         "children": [
            {"name": "10"}
         ]}
     ]}
]

# Then create num_loops instances of that loop
num_loops = 5
solving_loop = []
for i in range(num_loops):
   solving_loop.extend(single_loop.copy())

print(solving_loop)

# Create finalization
finalization = [
   {"name": "11",
    "children": [
      {"name": "12"}
    ]},
   {"name": "13"},
   {"name": "14"}
]

# Combine all of the metaslices
all_slices = []
all_slices.extend(initialization)
all_slices.extend(solving_loop)
all_slices.extend(finalization)

print(all_slices)

# Add to the root node
root_node["children"] = all_slices

print()
print(root_node)

# Write out
output_file = os.path.join(os.getcwd(), "mock_hierarchy.json")
with open(output_file, "w") as out_json:
   json.dump(root_node, out_json, indent=4)
