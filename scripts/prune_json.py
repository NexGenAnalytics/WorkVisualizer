import os
import json
import argparse

class DataPruner:

    def __init__(self, input_data: dict, rank: int, time_range: tuple = None):
        # Initialize the necessary lists
        self.pruned_json = []
        self.unpaired_ends = []

        # Save rank for sanity checks
        self.rank = rank

        # Initialize the depth of the call graph
        self.current_depth = 0
        self.max_depth = 0

        # Initialize json data
        self.json_data = input_data

        # Becomes true once we hit the first "event.begin"
        self.first_begin = False

        # Determine if we are only looking within a specific time range
        self.time_range = False
        if time_range is not None:
            self.start_time = time_range[0]
            self.end_time = time_range[1]
            self.time_range = True

        self.read_next_event = False
        self.previous_function_name = ""

    def parse_json(self):
        """
        To correctly match ends to begins, make sure that the data is sorted so that every 'end' occurs AFTER its corresponding 'begin' (ORDER BY time.offset)
        """
        iter = 0
        begin_counter, end_counter = 0,0
        total = len(self.json_data)
        unpaired_begins = []

        # Loop through all events to get necessary data
        for i in range(len(self.json_data)):

            event = self.json_data[i]

            if self.current_depth > self.max_depth:
                self.max_depth = self.current_depth

            if event["mpi.rank"] != self.rank:
                continue

            # Perform a sanity check
            assert self.rank == event["mpi.rank"]

            # Get the name of the MPI or Kokkos function
            # Also identify if it is beginning or ending the event
            begin = False
            if "event.begin#mpi.function" in event:
                begin, self.first_begin = True, True
                function_name = event["event.begin#mpi.function"]
            elif "event.begin#region" in event:
                begin, self.first_begin = True, True
                function_name = event["event.begin#region"]
            elif "event.end#mpi.function" in event:
                function_name = event["event.end#mpi.function"]
            elif "event.end#region" in event:
                function_name = event["event.end#region"]
            else:
                continue

            # Get the event time in seconds
            if "time.offset.ns" in event:
                event_time = event["time.offset.ns"] * 1e-9
            elif "time.offset" in event:
                event_time = event["time.offset"]
            else:
                raise ValueError("Could not identify time.offset[].ns value in event.")

            # Enforce the time constraints (if present)
            if self.time_range and not (self.start_time <= event_time <= self.end_time):
                continue

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

            # Get the size, src, or dst of an MPI Send or Recv
            dst, src, size = None, None, None
            if "MPI_Send" in function_name or "MPI_Isend" in function_name:

                # Find the next corresponding event with the dst info
                for j in range(1, len(self.json_data) - i):
                    next_event = self.json_data[i+j]
                    if "mpi.msg.dst" in next_event:
                        dst = next_event["mpi.msg.dst"]
                        size = next_event["mpi.msg.size"]
                        break

                    # Shouldn't take this long to find the match
                    elif j > 10:
                        break

            if "MPI_Recv" in function_name or "MPI_Irecv" in function_name:

                # Find the next corresponding event with the src info
                for j in range(1, len(self.json_data) - i):
                    next_event = self.json_data[i+j]
                    if "mpi.msg.src" in next_event:
                        src = next_event["mpi.msg.src"]
                        size = next_event["mpi.msg.size"]
                        break

                    # Shouldn't take this long to find the match
                    elif j > 10:
                        break

            # General filtering
            if "Kokkos Profile Tool Fence" in function_name or path.count("/") > 5:
                continue

            # Keep track of how many begins and ends there are
            if begin:
                begin_counter += 1
            else:
                end_counter += 1
                # Need to start on a "begin" or the algorithm doesn't make sense
                if not self.first_begin:
                    continue

            print(f"{iter}/{total}")
            print(event)

            # ----------------------------------------- BEGIN PAIRING PROCESS -----------------------------------------

            # Look for corresponding entry in either the begin or end lists
            paired = False
            if begin:
                event_footprint = {
                    "name": function_name,
                    "rank": event["mpi.rank"],
                    "begin_time": event_time,
                    "kernel_type": kernel_type,
                    "path": path,
                    "children": []
                }

                # Add send destination if applicable
                if "MPI_Send" in function_name or "MPI_Isend" in function_name:
                    if dst is not None:
                        event_footprint["dst"] = dst
                    if size is not None:
                        event_footprint["size"] = size

                # Add recv source if applicable
                if "MPI_Recv" in function_name or "MPI_Irecv" in function_name:
                    if src is not None:
                        event_footprint["src"] = src
                    if size is not None:
                        event_footprint["size"] = size

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

                              # Since we're closing the event, if it doesn't have children now it never will
                              if beginning["children"] == []:
                                del beginning["children"]
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
            iter += 1

        # Make sure all ends have been matched to a beginning
        # assert len(self.unpaired_ends) == 0
        print(f"There are {len(self.unpaired_ends)} unpaired endings.")
        print(f"The maximum depth is {self.max_depth}.")

        print()
        print(f"There are {begin_counter} begins and {end_counter} ends.")

        # Add the "main" function:
        self.pruned_json = {"name": "main", "children": self.pruned_json}

        # Finally, return the new JSON
        return self.pruned_json

def main():

    # Parse arguments
    parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
    parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
    parser.add_argument("-start", "--start_time", default=None, help="Beginning of time range of desired calls (i.e. beginning of a loop)")
    parser.add_argument("-end", "--end_time", default=None, help="End of time range of desired calls (i.e. end of a loop)")
    args = parser.parse_args()
    json_file = args.input
    start = float(args.start_time) if args.start_time is not None else None
    end = float(args.end_time) if args.end_time is not None else None

    # Create the desired time range
    time_range = (start, end) if start is not None and end is not None else None

    # Print a warning if the user gives a start and not end (or vice versa)
    if (start is not None or end is not None) and (end is None or start is None):
        print("Warning: Must provide both start and end times to specify the time range.")

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
    rank = int(file_splits[1].split("r")[0]) if "r_" in json_file else 0
    n_steps = int(file_splits[2].split("s")[0])

    # Create save directory
    current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "data", "pruned")
    os.makedirs(output_dir, exist_ok=True)

    # Read in all data
    trace_json_filepath = os.path.join(current_dir, json_file)
    f = open(trace_json_filepath)
    json_data = json.load(f)

    # Create DataPruner instance
    pruner = DataPruner(json_data, rank, time_range=time_range)
    pruned_json = pruner.parse_json()

    output_path = f"{output_dir}/{app_abr}_{rank}r_{n_steps}s_pruned.json"

    with open(output_path, "w") as out_json:
        json.dump(pruned_json, out_json)

    print(f"Process completed with {len(pruner.unpaired_ends)} unpaired ends.")

main()