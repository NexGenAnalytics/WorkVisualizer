import os
import json
import argparse
import numpy as np

"""
Takes in data for one of the following:
- One rank, for all timesteps
- All ranks, for one timestep

Then looks for anomalous behavior using the techniques developed in the plotting script.

Input filename should be formatted like:
- One rank (all timesteps) -> <app>_<rank>r_<n_steps>s_<misc>.json
- All ranks (one timestep) -> <app>_<n_procs>p_<step>s_<misc>.json

"""

class AnomalyDetector:

    def __init__(self, input_data: dict, rank_info: int, step_info: int, one_rank=False):
        """
        This class is intended to provide anomaly detection for two cases.
            1. One rank, all timesteps
            2. All ranks, one timestep

        In case 1, rank_info represents the rank ID and step_info tells how many time steps are present.
        In case 2, rank_info tells how many ranks were used, and step_info gives the number of the iteration.
        """
        # Identifies which case we're using
        self.one_rank_all_steps = one_rank

        # Initialize problem info
        self.rank_info = rank_info
        self.step_info = step_info

        # Save the input data
        self.json_data = input_data
        self.flattened_data = self.__get_flattened_dict()

        # Initialize dict to save any imbalanced timesteps
        self.imb_dict = {}

        # Set the imbalance threshold
        self.imb_threshold = 1e-4
        self.found_imbalance = False

    def find_imbalance(self):
        """
        Essentially the "main" function
        """
        # First, look at the case of one rank working on all timesteps
        if self.one_rank_all_steps:

            # This assumes that the JSON has already been trimmed to start right at the metaslice
            # ie this isn't the entire run

            # We need the period for this; for now, assume we have it
            self.period = 0.03

            # Get the start and end times for this rank
            start = self.json_data[0]["begin_time"]
            end = self.json_data[-1]["end_time"]

            # Create discrete time domain
            time_range = np.arange(start, end, period)

            # Count how many function calls are made in every time step
            step_iter = 0
            for timestep in time_range:
                count = sum(1 for event in self.json_data if (event["begin_time"] - period) <= event["begin_time"] < event["begin_time"] + period)
                step_iter += 1

            # this isn't great--it would be better to determine the pattern of functions
            #
            # for example: [ A E A C D E F A D A B E D A B E D A B E D A C E ]
            #   - where each letter represents a different function
            #   - should be able to find [ A B E D ] as the pattern

        # Then look at the case of all ranks working on one timestep
        else:

            # Initialize a counter
            rank_iter = [0] * self.rank_info

            # Note: The JSON is already trimmed to just show the data from that timestep
            for event in self.json_data:
                rank = event["rank"]

                # First event (for that rank) in this timestep
                if rank_iter[rank] = 0:
                    self.imb_dict[rank] = event["begin_time"]

                # Last event (for that rank) in this timestep (TODO improve this criterion)
                elif rank_iter[rank] = len(self.json_data) / self.rank_info
                    self.imb_dict[rank] -= event["end_time"]

                # Iterate the counter
                rank_iter[rank] = 1

            # Now self.imb_dict holds each rank ID and how long it took it to complete the iteration
            max_time = np.max(list(self.imb_dict.values()))
            avg_time = np.mean(list(self.imb_dict.values()))
            imbalance = (max_time / avg_time) - 1

            print(f"Found imbalance of {imbalance} across {self.rank_info} processors.")

            # TODO find a better way to report that imbalance was found
            if imbalance > self.imb_threshold:
                self.found_imbalance = True

            return imbalance, self.imb_dict

    def detect(self):
        # First look for imbalance
        imb = self.find_imbalance()

        # Then look for anyting else
        # bottleneck = self.find_bottleneck()

        # Package all anomalies into one container
        anomaly = imb

        # Then return whatever we found
        return anomalies

def main():
    # Parse command line arguments
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

    # Handle the two cases
    one_rank_all_steps = False
    if "p_" in json_file:
      rank_info = int(file_splits[1].split("p")[0]) # num procs
    elif "r_" in json_file:
      one_rank_all_steps = True
      rank_info = int(file_splits[1].split("r")[0]) # selected proc
    step_info = int(file_splits[2].split("s")[0])   # num steps or selected step

    # Read in all data
    json_filepath = os.path.join(os.getcwd(), json_file)
    f = open(json_filepath)
    json_data = json.load(f)

    # Create AnomalyDetector instance
    anomaly_detector = AnomalyDetector(json_data, rank_info, step_info, one_rank_all_steps)

    # Find any anomalies
    anomalies = anomaly_detector.detect()