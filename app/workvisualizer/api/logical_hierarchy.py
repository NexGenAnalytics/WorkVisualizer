#
# ************************************************************************
#
# Copyright (c) 2024, NexGen Analytics, LC.
#
# WorkVisualizer is licensed under BSD-3-Clause terms of use:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ************************************************************************
#
"""Create a hierarchy that shows the logical structure of the application (regardless of timesteps or repetitions)."""
import os
import json

class LogicalHierarchy:

    def __init__(self, events_file, ftn_id: int = -1, maximum_depth: int = -1):
        self.ftn_id = "" if ftn_id == -1 else ftn_id
        self.maximum_depth = maximum_depth
        self.root_name = ""
        self.handled_events = []

        self.hierarchy = {"name": "root", "children": []}

        f = open(events_file)
        self.unique_events = json.load(f)

        # Make sure the ftn_id exists
        if self.ftn_id != "":
            found_id = False
            for event in self.unique_events:
                if event["ftn_id"] == self.ftn_id:
                    found_id = True
                    break

            # TODO: improve warning/error handling
            # If we can't find the id, do the full hierarchy
            if not found_id:
                self.ftn_id = ""

    def create_hierarchy(self):
        found_root = True if self.ftn_id == "" else False
        for event in self.unique_events:

            if int(event["depth"]) + 1 >= self.maximum_depth:
                continue

            if event["ftn_id"] == self.ftn_id:
                self.hierarchy = event
                self.root_name = event["name"]
                self.hierarchy["children"] = []
                found_root = True

            if not found_root:
                print(f"ftn_id {event['ftn_id']}; root not found")
                continue

            if event["ftn_id"] in self.handled_events:
                continue

            elif self.ftn_id == "" or self.root_name in event["path"].split("/"):
                # Populate children_list at this level of path
                children_list = []
                self.handled_events.append(event["ftn_id"])
                for other_event in self.unique_events:
                    if other_event["path"] == event["path"]:
                        children_list.append(other_event)
                        self.handled_events.append(other_event["ftn_id"])

                # Take care of top level node
                if (event["path"] == self.root_name):
                    self.hierarchy["children"] = children_list

                else:
                    # Then find the parent
                    current_list = self.hierarchy["children"]
                    next_current_list = []
                    iter = 1
                    path_splits = event["path"].split("/")
                    if self.root_name != "":
                        target_idx = path_splits.index(self.root_name)
                        path_splits = path_splits[target_idx:]
                    for path_step in path_splits:
                        for parent in current_list:
                            if parent["name"] == path_step:
                                if iter == len(path_splits):
                                    parent["children"] = children_list
                                    break
                                else:
                                    next_current_list = parent["children"]
                        current_list = next_current_list
                        iter += 1

        return self.hierarchy

def generate_logical_hierarchy_from_root(events_file, output_file, ftn_id: int = -1, depth: int = -1):
    hierarchy_generator = LogicalHierarchy(events_file, ftn_id, maximum_depth=depth)
    hierarchy = hierarchy_generator.create_hierarchy()

    logical_dir = os.path.dirname(output_file)
    os.makedirs(logical_dir, exist_ok=True)

    with open(output_file, "w") as out_json:
        json.dump(hierarchy, out_json, indent=1)
