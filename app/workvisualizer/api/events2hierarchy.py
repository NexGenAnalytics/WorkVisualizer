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
import os
import json
import argparse

"""
Takes in the output of cali2json and creates a nested hierarchy.
"""

class DataPruner:

    def __init__(self, input_data: dict, time_range: tuple=None):
        # Initialize the lists
        self.hierarchical_json = []
        self.queue = []

        # Current dict
        self.previous_event_dict = None
        self.current_event_dict = None

        # Initialize the json data
        self.json_data = input_data

        # Determine if we only want a specific time range
        self.time_range = False
        if time_range is not None:
            self.start_time = time_range[0]
            self.end_time = time_range[1]
            self.time_range = True

        # Initialize end times list
        self.end_times = []

    def __add_event_to_parent(self, parent, event):
        if 'children' not in parent:
            parent['children'] = []
        parent['children'].append(event)

    def __find_parent_for_event(self, event, potential_parents):
        for parent in reversed(potential_parents):  # Check in reverse order for the latest possible parent
            if parent['ts'] <= event['ts'] < (parent['ts'] + parent['dur']):
                return parent
        return None

    def parse_json(self):
        """Generates the hierarchy"""

        nested_events = []
        active_parents = []

        for event in self.json_data:
            parent = self.__find_parent_for_event(event, active_parents)
            if parent:
                self.__add_event_to_parent(parent, event)
            else:
                nested_events.append(event)

            active_parents.append(event)

            # Clean up the active_parents list to remove any events that have finished
            active_parents = [e for e in active_parents if e['ts'] + e['dur'] > event['ts']]

        # print(nested_events)
        return nested_events

def events_to_hierarchy(input_file, output_file, time_range: tuple=None):

    f = open(input_file)
    json_data = json.load(f)

    # Create DataPruner instance
    pruner = DataPruner(json_data, time_range=time_range)
    pruned_json = pruner.parse_json()

    # Format correctly
    output_json = {"name": "root", "children": pruned_json}

    with open(output_file, "w") as out_json:
        json.dump(output_json, out_json, indent=4)

    print(f"Process completed successfully.")
