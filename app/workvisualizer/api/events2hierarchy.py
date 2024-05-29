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
