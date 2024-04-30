import os
import json
import argparse

class DataPruner:

    def __init__(self, input_data: dict, rank: int):
        # Initialize the necessary lists
        self.pruned_json = []
        self.unpaired_ends = []

        # Save rank for sanity checks
        self.rank = rank

        # Initialize the depth of the call graph
        self.current_depth = 0

        # Initialize json data
        self.json_data = input_data


    def parse_json(self):
        """
        To correctly match ends to begins, make sure that the data is sorted so that every 'end' occurs AFTER its corresponding 'begin' (ORDER BY time.offset)
        """
        # Loop through all events to get necessary data
        for event in self.json_data:

            # Perform a sanity check
            assert self.rank == event["mpi.rank"]

            # Get the name of the MPI or Kokkos function
            # Also identify if it is beginning or ending the event
            begin = False
            if "event.begin#mpi.function" in event:
                begin = True
                function_name = event["event.begin#mpi.function"]
            elif "event.begin#region" in event:
                begin = True
                function_name = event["event.begin#region"]
            elif "event.end#mpi.function" in event:
                function_name = event["event.end#mpi.function"]
            elif "event.end#region" in event:
                function_name = event["event.end#region"]
            else:
                continue

            print(event)

            # Get the event time in seconds
            if "time.offset.ns" in event:
                event_time = event["time.offset.ns"] * 1e-9
            elif "time.offset" in event:
                event_time = event["time.offset"]
            else:
                raise ValueError("Could not identify time.offset[].ns] value in event.")

            # Get the kernel_type and store for later
            if "kernel_type" in event:
                kernel_type = event["kernel_type"]
            else:
                kernel_type = ""

            # Get the path and store for later
            if "path" in event:
                path = event["path"]
            else:
                path = ""

            # ----------------------------------------- BEGIN PAIRING PROCESS -----------------------------------------

            # Look for corresponding entry in either the begin or end lists
            paired = False
            if begin:
                event_footprint = {
                    "name": function_name,
                    "begin_time": event_time,
                    "kernel_type": kernel_type,
                    "path": path,
                    "children": []
                }
                if self.current_depth > 0:
                    current_list = self.pruned_json
                    for _ in range(self.current_depth):
                        most_recent_begin_dict = current_list[-1]
                        current_list = most_recent_begin_dict["children"]
                    current_list.append(event_footprint)
                else:
                    self.pruned_json.append(event_footprint)

                self.current_depth += 1

            else:
                # Loop through all unpaired begins
                root_list = self.pruned_json
                for depth in range(self.current_depth):
                    if depth == 0:
                        root_list = root_list
                    else:
                        most_recent_begin_dict = root_list[-1]
                        root_list = most_recent_begin_dict["children"]

                    for beginning in root_list:

                        # Generate the "path" variable to compare against
                        comp_path = beginning["path"] + "/" + function_name if beginning["path"] != "" else function_name

                        # Try to find a match for all relevant info
                        if "end_time" not in beginning and \
                          beginning["name"] == function_name and \
                          beginning["kernel_type"] == kernel_type and \
                          comp_path == path:
                              beginning["end_time"] = event_time
                              beginning["duration"] = event_time - beginning["begin_time"]
                              paired = True
                              break

                if paired:
                    print(f"    FOUND A MATCH FOR {function_name}")
                    self.current_depth -= 1

                # Otherwise, add event info to unpaired ends (CURRENTLY, THIS SHOULD NEVER HAPPEN)
                else:
                    event_footprint = {
                        "name": function_name,
                        "end_time": event_time,
                        "kernel_type": kernel_type,
                        "path": path
                    }
                    self.unpaired_ends.append(event_footprint)

            print()

        # Make sure all ends have been matched to a beginning
        assert len(self.unpaired_ends) == 0

        # Finally, return the new JSON
        return self.pruned_json

def main():

    # Parse arguments
    parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
    parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
    args = parser.parse_args()
    json_file = args.input

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
    rank = int(file_splits[1].split("r")[0])
    n_steps = int(file_splits[2].split("s")[0])

    # Create save directory
    current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "data", app)
    os.makedirs(output_dir, exist_ok=True)

    # Read in all data
    trace_json_filepath = os.path.join(current_dir, json_file)
    f = open(trace_json_filepath)
    json_data = json.load(f)

    # Create DataPruner instance
    pruner = DataPruner(json_data, rank)
    pruned_json = pruner.parse_json()

    output_path = f"{output_dir}/{app_abr}_{rank}r_{n_steps}s_pruned.json"

    with open(output_path, "w") as out_json:
        json.dump(pruned_json, out_json)

    print(f"Process completed with {len(pruner.unpaired_ends)} unpaired ends.")

main()