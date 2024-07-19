"""Create a hierarchy that shows the logical structure of the application (regardless of timesteps or repetitions)."""
import os
import json

class LogicalHierarchy:

    def __init__(self, events_file, ftn_id: int = -1):
        self.ftn_id = "" if ftn_id == -1 else ftn_id
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
                        names_of_current_list = [e["name"] for e in current_list]
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

def generate_logical_hierarchy_from_root(events_file, output_file, ftn_id: int = -1):
    hierarchy_generator = LogicalHierarchy(events_file, ftn_id)
    hierarchy = hierarchy_generator.create_hierarchy()

    logical_dir = os.path.dirname(output_file)
    os.makedirs(logical_dir, exist_ok=True)

    with open(output_file, "w") as out_json:
        json.dump(hierarchy, out_json, indent=1)
