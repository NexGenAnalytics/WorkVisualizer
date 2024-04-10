"""Plots the MPI and Kokkos data over time."""


import os
import json
import argparse
import numpy as np
from scipy.fft import fft, fftfreq, fftshift
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib import colormaps


"""
Takes in a trace json and outputs the frequency of a given call.

Steps to recreate:
  - export KOKKOS_TOOLS_LIBS=/path/to/libcaliper.so
  - export CALI_CONFIG_FILE=/path/to/caliper.config
  - <run program>
        - MiniEM:    mpirun -n 4 ./PanzerMiniEM_BlockPrec.exe --numTimeSteps=10
        - ExaMiniMD: mpirun -np 4 -bind-to socket ./ExaMiniMD -il ../input/in.lj --comm-type MPI --kokkos-map-device-id-by=mpi_rank
        - ExaMPM:    mpirun -n 4 ./DamBreak 0.05 2 0 0.1 1.0 10 serial
  - touch em_4p_100s_alltrace.json
        - Format: <app>_<num_procs>p_<num_steps>s_<all/mpi>trace.json)
  - cali-query -q "SELECT * FORMAT json" *.cali | tee em_4p_100s_alltrace.json
  - <move resulting json to this directory>
"""


######################################################################################################################
#################                                                                                    #################
#################                                       SET UP                                       #################
#################                                                                                    #################
######################################################################################################################


# Define a key to sort all of the functions
def sort_all_functions(function_name, collective_list):
    if function_name in collective_list:
       return 0
    elif "MPI_" in function_name:
        return 1
    else:
        return 2

# Parse command line arg for the json file
parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
parser.add_argument("-s", "--save", action="store_true", help="Whether or not to save the plot to a file.")
parser.add_argument("-e", "--expected", default=None, help="The expected frequency of a given dataset (i.e. the value that should be found by the WV.)")
parser.add_argument("-p", "--proc", default=-1, help="Processor to be plotted. Defaults to all available processors.")
parser.add_argument("-t", "--target", default=0, help="Processor to be colored in (when all procs are plotted). Defaults to first processor.")
parser.add_argument("-o", "--order", action="store_true", help="Whether or not to sort the functions in the resulting plots.")
parser.add_argument("-b", "--bin_count", default=1000, help="Number of timesteps into which to bin the full application duration for frequency analysis.")

# Read in all arguments
args = parser.parse_args()
json_file = args.input
save = args.save
expected_freq = args.expected
num_bins = int(args.bin_count)
output_proc = int(args.proc)
order = args.order
target_proc = int(args.target)

# Get problem info
file_splits = json_file.split("_")
app_abr = file_splits[0].lower()
if app_abr == "mpm" or app_abr == "exampm":
    app = "ExaMPM"
elif app_abr == "md" or app_abr == "examinimd":
    app = "ExaMiniMD"
elif app_abr == "em" or app_abr == "miniem":
    app = "MiniEM"
else:
    app = app_abr
n_procs = int(file_splits[1].split("p")[0])
n_steps = int(file_splits[2].split("s")[0])
call_type = "MPI" if "mpi" in file_splits[3].lower() else "All"

# Create save directory
current_dir = os.getcwd()
output_dir = os.path.join(current_dir, "plots", app)
os.makedirs(output_dir, exist_ok=True)

# Create list of all MPI collective functions
all_collectives = ["MPI_Allgather", "MPI_Allgatherv", "MPI_Allreduce", "MPI_Alltoall",
                   "MPI_Alltoallv", "MPI_Alltoallw", "MPI_Barrier", "MPI_Bcast",
                   "MPI_Gather", "MPI_Gatherv", "MPI_Iallgather", "MPI_Iallreduce",
                   "MPI_Ibarrier", "MPI_Ibcast", "MPI_Igather", "MPI_Igatherv",
                   "MPI_Ireduce", "MPI_Iscatter", "MPI_Iscatterv", "MPI_Reduce",
                   "MPI_Scatter", "MPI_Scatterv", "MPI_Exscan", "MPI_Op_create",
                   "MPI_Op_free", "MPI_Reduce_local", "MPI_Reduce_scatter", "MPI_Scan",
                   "MPI_User_function"]

# Read in all Allreduce calls
trace_json_filepath = os.path.join(current_dir, json_file)
f = open(trace_json_filepath)
json_data = json.load(f)

# Initialize all timings
all_times = {}

# Get all ranks' init time
all_init_times = [0.] * n_procs

# Loop through all events to isolate relevant calls
for event in json_data:
    rank = event["mpi.rank"]
    begin_time = event["time.offset.ns"] * 1e-9 # convert to seconds

    # Get name of MPI function or Kokkos kernel
    if "event.begin#mpi.function" in event:
        function_name = event["event.begin#mpi.function"]
    elif "event.begin#region" in event:
        function_name = event["event.begin#region"]
    else:
        continue

    # Handle default case
    if function_name not in all_times.keys():
        all_times.setdefault(function_name, {proc: [] for proc in range(n_procs)})

    # Add to datasets
    all_times[function_name][rank].append(begin_time)

    # Also add MPI_Init time to all_init_times to fix offset later
    if function_name == "MPI_Init":
        all_init_times[rank] = begin_time

# Determine offset among ranks (resolved while plotting)
true_time = min(all_init_times)
offsets = [init_time - true_time for init_time in all_init_times]

for function_name, rank_times in all_times.items():
    for rank, timestamps in rank_times.items():
        # Correct timestamps for the given rank
        all_times[function_name][rank] = [timestamp - offsets[rank] - true_time for timestamp in timestamps]


######################################################################################################################
#################                                                                                    #################
#################                                 GENERATE TIME PLOT                                 #################
#################                                                                                    #################
######################################################################################################################


# Initialize info
all_functions = sorted(all_times.keys(), key=lambda func: sort_all_functions(func, all_collectives)) if order else all_times.keys()
increment = 1.0 / len(all_functions)
target_functions = []
target_increments = []

# Initialize grey color map for background ranks
background_colors = colormaps["Greys_r"](np.linspace(0, 1, n_procs + 1))

# Move the target_rank to the end of the list so it is plotted last
ranks_list = [rank for rank in range(n_procs)]
ranks_list.append(ranks_list.pop(ranks_list.index(target_proc)))

# Generate plots
plt.figure()
mpi_iter, kokkos_iter, collective_iter = 0, 0, 0
for rank in ranks_list:

    # Create plots for specified ranks
    if output_proc == -1 or rank == output_proc:
        iter = 1

        # Loop through all functions called by the current rank
        for function in all_functions:
            current_increment = iter * increment

            if call_type == "MPI" and function.replace("MPI_","") not in target_functions:
                target_functions.append(function.replace("MPI_",""))
                target_increments.append(current_increment)

            # Get the data for the current function at the current rank
            times_list = all_times[function][rank]
            x_data = np.array(times_list)

            # Plot at arbitrary y-value
            y_data = np.zeros_like(x_data) + current_increment
            size = [10] * len(times_list)

            # Determine if this is the target rank (and if so, color the datapoints)
            if rank == output_proc or rank == target_proc:
                mpi = True if "MPI_" in function else False
                if mpi:
                    if function in all_collectives:
                        label = f"Rank {rank} Collective MPI Call" if collective_iter == 0 else None
                        color = "tab:green"
                        collective_iter += 1
                    else:
                        label = f"Rank {rank} MPI Call" if mpi_iter == 0 else None
                        color = "tab:blue"
                        mpi_iter += 1
                else:
                    label = f"Rank {rank} Kokkos Call" if kokkos_iter == 0 else None
                    color = "tab:orange"
                    kokkos_iter += 1
            else:
                label = f"Rank {rank}" if iter == 1 else None
                color = background_colors[rank]

            # Create time plots
            plt.scatter(x_data, y_data, size, color=color, label=label)

            # Update iter so rank label only prints once and y-vals are different
            iter += 1

    # Ignore ranks that user did not specify
    else:
      continue

# Format legend box
num_labels = len(plt.gca().get_legend_handles_labels()[1])
plt.legend(loc="upper right", ncols=num_labels//3)

# Format axes
plt.ylim(0,(1 + (2 * increment)))
plt.yticks(target_increments, target_functions)
plt.xlabel("Time (s)")

# Format titles
output_proc_string = f"{n_procs} Ranks" if output_proc == -1 else f"Rank {output_proc}"
plt.suptitle(f"{app} {call_type} Calls Over Time", fontweight="bold", fontsize=15)
plt.title(f"{output_proc_string}, {n_steps} Timesteps", style="italic")

# Output the plot
if save:
    plt.savefig(f"{output_dir}/{n_procs}p_{n_steps}s_{call_type.lower()}.png")
plt.show()
plt.close()


######################################################################################################################
#################                                                                                    #################
#################                                 FREQUENCY ANALYSIS                                 #################
#################                                                                                    #################
######################################################################################################################


# For simplicity, only look at one target_function for now
target_function = "MPI_Send"
target_times_dict = all_times[target_function]

# Determine time range
all_target_times = np.concatenate(list(target_times_dict.values()))
min_time = np.min(all_target_times)
max_time = np.max(all_target_times)

# Plot number of instances of each rank at each timestep
binned_data = {}
for rank in range(n_procs):
    timestamps = target_times_dict[rank]
    counts, binned_times = np.histogram(timestamps, bins=num_bins)
    binned_data[rank] = [binned_times, counts]
    plt.plot(binned_times[:-1], counts, label=f"Rank {rank}")
plt.suptitle(f"{app} Counts of {target_function}", fontweight="bold", fontsize=15)
plt.title(f"{num_bins} bins", style="italic")
plt.xlabel("Time (s)")
plt.ylabel("Counts")
plt.legend(loc="upper right")
plt.show()
plt.close()

# Try calculating manually
# specific_rank = 3
# specific_times = target_times_dict[specific_rank]
# time_range = (min(specific_times), max(specific_times))
# duration = (time_range[1] - time_range[0])
# num_instances = len(specific_times)
# print(f"{num_instances} instances of {target_function} in {duration} seconds.")
# period = duration / num_instances
# print(f"  That's a period of one instance per {period} seconds, compared to the known period of {known_periods[specific_rank]}.")
# print(f"  That's a frequency of {1/period} Hz, compared to the known freq of {known_freqs[specific_rank]}.")

rank_periods = {}
sum_periods = 0.
# Then do a Fourier Transform
for rank in range(n_procs):
    duration = max(target_times_dict[rank]) - min(target_times_dict[rank])
    sr = num_bins / duration
    x = binned_data[rank][1]
    X = fftshift(fft(x)) * sr / len(x)
    N = len(X)
    n = np.arange(N)
    T = N/sr
    freq = np.linspace(-sr/2, sr/2, N, endpoint=False)

    # Determine peak frequency
    sorted_indices = np.argsort(np.abs(X))
    peak_freq = np.abs(freq[sorted_indices[-2]]) # max will be at 0, so we want the second max
    peak_T = 1/peak_freq
    point = [peak_freq, np.abs(X)[sorted_indices[-2]]]

    calc_plot = plt.plot(freq, np.abs(X), label=f"Rank {rank} calculated freq: {peak_freq} Hz, period: {peak_T} s")
    color = calc_plot[0].get_color()
    plt.scatter(point[0], point[1], 60, marker="o", color="black", facecolors="none", label="Peak frequency" if rank == n_procs-1 else None)

    rank_periods[rank] = peak_T
    sum_periods += peak_T

# Generate the FFT plot
plt.xlabel("Frequency (Hz)")
plt.ylabel("FFT Magnitude |X(freq)|")
plt.suptitle(f"FFT of {target_function} Calls", fontweight="bold", fontsize=15)
plt.title(f"{num_bins} bins", style="italic")
plt.legend(loc="upper right")
plt.grid(True)
plt.show()
plt.close()

q1 = np.quantile(list(rank_periods.values()), 0.25)
q3 = np.quantile(list(rank_periods.values()), 0.75)
iqr = q3 - q1
# low_threshold = q1 - iqr # could check for super fast ranks
high_threshold = q3 + iqr
outlier_ranks = []
sum_periods_without_outliers = 0.
for rank in range(n_procs):
    if rank_periods[rank] > high_threshold:
        outlier_ranks.append(rank)
    else:
        sum_periods_without_outliers += rank_periods[rank]
if len(outlier_ranks) > 0:
    print(f"Outlier ranks: {outlier_ranks}")
    for rank in outlier_ranks:
        print(f"  Rank {rank} had a period of {rank_periods[rank]} s")
else:
    print("No outlier ranks found.")

average_period_without_outliers = sum_periods_without_outliers / (n_procs - len(outlier_ranks))
print(f"Average period (excluding any outliers): {average_period_without_outliers} s")
