"""Create a hierarchy that shows the logical structure of the application (regardless of timesteps or repetitions)."""
import os
import json

class LogicalHierarchy:

    def __init__(self, ftn_id: str = ""):
        self.ftn_id = ftn_id
        print("ftn_id: ", self.ftn_id)
        self.root_name = ""
        self.handled_events = []

        self.hierarchy = {"name": "root", "children": []}

        f = open(os.path.join(os.getcwd(), "files", "unique_events.json"))
        self.unique_events = json.load(f)

    def create_hierarchy(self):
        found_root = False
        for event in self.unique_events:

            if event["ftn_id"] == self.ftn_id:
                self.hierarchy = event
                self.root_name = event["name"]
                self.hierarchy["children"] = []
                found_root = True

            if not found_root:
                print(f"eid {event['eid']}; root not found")
                continue

            if event["eid"] in self.handled_events:
                continue

            elif self.ftn_id == "" or self.root_name in event["path"].split("/"):
                print("event[name]: ", event["name"])
                print(event["path"].split("/"))
                print("self.root_name in event['path'].split('/'): ", self.root_name in event["path"].split("/"))
                print("--------------------------------------")
                print(f"Creating children list for {event['eid']}")
                print(f"  Path: {event['path']}")
                # Populate children_list at this level of path
                children_list = []
                self.handled_events.append(event["eid"])
                for other_event in self.unique_events:
                    if other_event["path"] == event["path"]:
                        children_list.append(other_event)
                        self.handled_events.append(other_event["eid"])

                print()
                print(f"All events with same path: {event['path']}")
                print_list = [e["eid"] for e in children_list]
                print(print_list)
                print()

                # Take care of top level node
                if (event["path"] == self.root_name):
                    self.hierarchy["children"] = children_list

                else:
                    # Then find the parent
                    current_list = self.hierarchy["children"]
                    next_current_list = []
                    iter = 1
                    path_splits = event["path"].split("/")
                    print("path_splits: ", path_splits)
                    if self.root_name != "":
                        target_idx = path_splits.index(self.root_name)
                        path_splits = path_splits[target_idx:]
                        print("sliced path splits: ", path_splits)
                    for path_step in path_splits:
                        names_of_current_list = [e["name"] for e in current_list]
                        # print(f"Looking for {path_step} in {names_of_current_list}")
                        for parent in current_list:
                            if parent["name"] == path_step:
                                print(f"Found a parent: {parent['name']}")
                                if iter == len(path_splits):
                                    parent["children"] = children_list
                                    break
                                else:
                                    next_current_list = parent["children"]
                        current_list = next_current_list
                        iter += 1

        return self.hierarchy

def generate_logical_hierarchy_from_root(output_file, ftn_id: str = ""):
    hierarchy_generator = LogicalHierarchy(ftn_id)
    hierarchy = hierarchy_generator.create_hierarchy()

    with open(output_file, "w") as out_json:
        json.dump(hierarchy, out_json, indent=1)
