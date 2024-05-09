"""Plots the MPI and Kokkos data over time."""


import os
import json
import pandas as pd
import argparse
import numpy as np
from math import isclose
from scipy.stats import mode
from scipy.signal import find_peaks
from scipy.fft import fft, fftshift
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

# For adjusting the lightness of colors in the final plot
def adjust_lightness(color, amount=0.5):
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])

# Set time constraint based on requested metaslice
def time_constraint(begin_time, metaslice):
    if metaslice == "init":
        return 0 < begin_time < 10
    elif metaslice == "iter":
        return 15.20 < begin_time < 15.50
    elif metaslice == "loop":
        return 10 < begin_time < 39
    elif metaslice == "final":
        return begin_time > 39
    else:
        return begin_time > 0

def signal_to_noise(input_data):
    a = np.asanyarray(input_data)
    mean = np.mean(a)
    std = np.std(a)
    return np.where(std == 0, 0, mean/std)

def sort_functions(function_name, sorting_dict, sorting_key):
    # Average across all ranks
    if sorting_key not in sorting_dict:
        raise ValueError(f"{sorting_key} not recognized. Use 'path' or 'duration'.")
    return np.mean(sorting_dict[sorting_key][function_name])

# Parse command line arg for the json file
parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
parser.add_argument("-s", "--save", action="store_true", help="Whether or not to save the plot to a file.")
parser.add_argument("-a", "--all", action="store_true", help="Whether or not to plot ALL functions on the final plot (and not just the periodic ones).")
parser.add_argument("-f", "--filtered", action="store_true", help="Plots only the FILTERED functions on the final plot.")
parser.add_argument("-sort", "--sorting_key", default=None, help="`path`, `call`, or `rank`")
parser.add_argument("-dt", "--draw_timesteps", action="store_true", help="Whether or not to draw the timesteps on the final plot.")
parser.add_argument("-dm", "--draw_macroloops", action="store_true", help="Whether or not to draw the macroloopss on the final plot.")
parser.add_argument("-p", "--proc", default=-1, help="Processor to be plotted. Defaults to all available processors.")
parser.add_argument("-t", "--target", default=0, help="Processor to be colored in (when all procs are plotted). Defaults to first processor.")
parser.add_argument("-b", "--bin_count", default=1000000, help="Number of timesteps into which to bin the full application duration for frequency analysis.")
parser.add_argument("-m", "--metaslice", default="all", help="init, loop, final, or all")
parser.add_argument("-v", "--vertical", action="store_true", help="Plots the calls over time plot vertically (to sync visually with the calltree).")

# Read in all arguments
args = parser.parse_args()
json_file = args.input
save = args.save
num_bins = int(args.bin_count)
draw_timesteps = args.draw_timesteps
draw_macroloops = args.draw_macroloops
output_proc = int(args.proc)
plot_all_functions = args.all
plot_filtered_functions = args.filtered
sorting_key = args.sorting_key.lower()
target_proc = int(args.target)
metaslice = args.metaslice
vertical_plot = args.vertical

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
n_procs = int(file_splits[1].split("p")[0]) if "p_" in json_file else 1
n_steps = int(file_splits[2].split("s")[0])

# Determine sorting key
if sorting_key is None:
    yaxis_label = "Default Ordering (read-in sequence)"
elif sorting_key == "path":
    yaxis_label = "-----> Increasing Depth in the Path ----->"
elif sorting_key == "rank":
    yaxis_label = f"Functions ordered by Rank (0 --> {n_procs})"
elif sorting_key == "duration":
    yaxis_label = "-----> Increasing Time Spent in Each Function ----->"
elif sorting_key == "call":
    yaxis_label ="Functions ordered by call type (MPI Collective -> MPI -> Kokkos)"
else:
    print(f" Sorting key {sorting_key} not recongized; using the default ordering instead. Supported keys: 'path', 'call', 'rank'.")
    sorting_key = None
    yaxis_label = "Default Ordering (read-in sequence)"

# Create save directory
current_dir = os.getcwd()
output_dir = os.path.join(current_dir, "plots", app, metaslice)
os.makedirs(output_dir, exist_ok=True)

# Create list of all MPI collective functions for reference if needed
all_collectives = ["MPI_Allgather", "MPI_Allgatherv", "MPI_Allreduce", "MPI_Alltoall",
                   "MPI_Alltoallv", "MPI_Alltoallw", "MPI_Barrier", "MPI_Bcast",
                   "MPI_Gather", "MPI_Gatherv", "MPI_Iallgather", "MPI_Iallreduce",
                   "MPI_Ibarrier", "MPI_Ibcast", "MPI_Igather", "MPI_Igatherv",
                   "MPI_Ireduce", "MPI_Iscatter", "MPI_Iscatterv", "MPI_Reduce",
                   "MPI_Scatter", "MPI_Scatterv", "MPI_Exscan", "MPI_Op_create",
                   "MPI_Op_free", "MPI_Reduce_local", "MPI_Reduce_scatter", "MPI_Scan",
                   "MPI_User_function"]

# Read in all data
trace_json_filepath = os.path.join(current_dir, json_file)
f = open(trace_json_filepath)
json_data = json.load(f)

# Initialize all timings and counts
all_times = {}
function_total_counts = {}
sorting_dict = {"path": {}, "call": {}, "rank": {}, "duration": {}}
begin_times_dict = {}
end_times_dict = {}

# Get all ranks' init time
all_init_times = [0.] * n_procs
program_max_time = 0.
program_min_time = 0. # we enforce this later when dealing with the offset

longest_duration = ["", 0.]

# Move the target_rank to the end of the list so it is plotted last
ranks_list = [rank for rank in range(n_procs)]
ranks_list.append(ranks_list.pop(ranks_list.index(target_proc)))

# Loop through all events to isolate relevant calls
for event in json_data:
    rank = event["mpi.rank"]
    begin_time = event["time.offset.ns"] * 1e-9 # convert to seconds

    # Get name of MPI function or Kokkos kernel
    if time_constraint(begin_time, metaslice) and "event.begin#mpi.function" in event:
        function_name = event["event.begin#mpi.function"]

    elif time_constraint(begin_time, metaslice) and "event.begin#region" in event:
        function_name = event["event.begin#region"]

    else:
        continue

    # Append the depth of the path to the function name
    if "path" in event:
        if event['path'].count('/') + 1 > 20:
            continue
        function_name += f" Path {event['path'].count('/') + 1}"
    else:
        function_name += " Path 0"

    # Append the rank to the function name
    function_name += f" Rank {event['mpi.rank']}"

    # Add to times dict
    if function_name not in all_times:
        all_times.setdefault(function_name, [])
    all_times[function_name].append(begin_time)

    # Add to counts dict
    if function_name not in function_total_counts:
        function_total_counts.setdefault(function_name, 0)
    function_total_counts[function_name] += 1

    # Update max time
    if begin_time > program_max_time:
        program_max_time = begin_time

    # Also add MPI_Init time to all_init_times to fix offset later
    if function_name == "MPI_Init":
        all_init_times[rank] = begin_time

    # Populate the sorting dict
    if sorting_key is not None:
        if function_name not in sorting_dict[sorting_key]:
            sorting_dict[sorting_key].setdefault(function_name, 0)

        # Sort by path
        if sorting_key == "path":
            sorting_val = 0 if "path" not in event else event["path"].count("/") + 1

        # Sort by rank
        elif sorting_key == "rank":
            sorting_val = rank

        # Sort by call type
        elif sorting_key == "call":
            sorting_val = 0 if function_name.split(" Path ")[0] in all_collectives else (1 if "MPI" in function_name else 2)

        # Add sorting value to the sorting dict
        sorting_dict[sorting_key][function_name] = sorting_val


# Correct the offset among ranks
true_time = min(all_init_times)
offsets = [init_time - true_time for init_time in all_init_times]
for function_name, function_times in all_times.items():
    rank = int(function_name.split(" Rank ")[-1])
    all_times[function_name] = [time - offsets[rank] - true_time for time in function_times]

# Get the data for ALL functions before filtering down
all_functions = list(all_times.keys())
all_function_counts = np.array(list(function_total_counts.values()))
all_function_names = np.array(list(function_total_counts.keys()))
total_num_functions = len(all_function_names)
max_sort_indices = np.flip(np.argsort(all_function_counts)) # to get in descending order
sorted_names = all_function_names[max_sort_indices]

# Only take functions in the top <percent>% of counts
if total_num_functions > 100:
    percent = 0.02
    num_pruned_functions = int(percent * total_num_functions)
    pruned_functions = sorted_names[:num_pruned_functions]
    print(f"There are {len(all_functions)} total, but we filter down to the {num_pruned_functions} most frequent functions for analysis.")

else:
    pruned_functions = sorted_names
    print(f"Keeping all {total_num_functions} functions for initial analysis.")

######################################################################################################################
#################                                                                                    #################
#################                                 FREQUENCY ANALYSIS                                 #################
#################                                                                                    #################
######################################################################################################################


# Store all periods for analysis later
all_periods = {}
function_analysis = {} # this can be simplified if we only care about PTM

# Look at each target_function
for target_function in pruned_functions:

    # ----------------------------------------------------------------------------------------------------------------
    # BINS

    # Make sure that the function exists
    if target_function not in all_times:
        continue

    # Determine time range
    all_target_times = all_times[target_function]
    min_time = np.min(all_target_times)
    max_time = np.max(all_target_times)

    # Could mean that each processor just called it once
    if len(all_target_times) == n_procs:
        continue

    # Plot number of instances of each rank at each timestep
    timestamps = all_target_times
    counts, binned_times = np.histogram(timestamps, bins=num_bins)
    binned_data = [binned_times, counts]
    #     plt.plot(binned_times[:-1], counts, label=f"Rank {rank}")
    # plt.suptitle(f"{app} Counts of {target_function} ({metaslice.capitalize()} phase)", fontweight="bold", fontsize=15)
    # plt.title(f"{num_bins} bins", style="italic")
    # plt.xlabel("Time (s)")
    # plt.ylabel("Counts")
    # plt.legend(loc="upper right")
    # if save:
    #     plt.savefig(f"{output_dir}/{n_procs}p_{n_steps}s_{target_function.replace('MPI_','').lower()}_{num_bins:.0e}bins_time_{metaslice}.png")
    # plt.show()
    # plt.close()

    # ----------------------------------------------------------------------------------------------------------------
    # FFT

    print(target_function)

    sum_periods = 0.
    max_freq = 0.
    max_mag = 0.

    # Protects against case where one rank is working while others aren't
    func_all_snr, func_all_ptm, func_all_std = [], [], []

    # Get period for each rank
    duration = max(timestamps) - min(timestamps)

    if duration == 0:
        continue

    sr = num_bins / duration
    x = binned_data[1]
    X = fftshift(fft(x)) * sr / len(x)
    N = len(X)
    n = np.arange(N)
    T = N/sr
    freq = np.linspace(-sr/2, sr/2, N, endpoint=False)

    # Determine peak frequency (find highest freqs and see if they are peaks)
    sorted_indices = np.argsort(np.abs(X))
    peaks, _ = find_peaks(np.abs(X))

    max_freq_index = sorted_indices[-2]  # set as default (ignoring peak at 0 Hz)
    for i in range(sorted_indices.size - 1):
        index = -2 - i
        if sorted_indices[index] in peaks:
            max_freq_index = sorted_indices[index]

            # Now see if there is a similar peak at half of this frequency
            next_indices = [index - j for j in range(1, 4)]
            for next_index in next_indices:
                if sorted_indices[next_index] in peaks and isclose(np.abs(freq[sorted_indices[next_index]]), np.abs(freq[max_freq_index] / 2), rel_tol=1e-2):
                    max_freq_index = sorted_indices[next_index]
                    break # Use the half frequency as the max

            break  # Use the original max_freq_index

        if i > 5:
            break  # Something has gone wrong

    peak_freq = np.abs(freq[max_freq_index])
    # half_freq_index = np.where(freq == peak_freq / 2)
    # print(f"np.abs(X)[half_freq_index]: {np.abs(X)[half_freq_index]}")
    # print(f"np.abs(X)[max_freq_index]:  {np.abs(X)[max_freq_index]}")
    # if np.abs(X)[half_freq_index] and isclose(np.abs(X)[half_freq_index], np.abs(X)[max_freq_index], rel_tol=1e-2):
    #     max_freq_index = half_freq_index
    peak_T = 1/peak_freq
    peak_mag = np.abs(X)[max_freq_index]
    point = [peak_freq, peak_mag]

    snr = signal_to_noise(np.abs(X))
    ptm = peak_mag / np.mean(np.abs(X))
    std = np.std(np.abs(X))
    if np.isnan(ptm):
        ptm = 0

    # rank_periods[rank] = peak_T
    sum_periods += peak_T

    if peak_freq > max_freq:
        max_freq = peak_freq

    if peak_mag > max_mag:
        max_mag = peak_mag

    func_all_snr.append(snr)
    func_all_ptm.append(ptm)
    func_all_std.append(std)

    all_periods[target_function] = peak_T
    #     if period > high_threshold:
    #         outlier_ranks.append(rank)
    #     else:
    #         sum_periods_without_outliers += period
    # if len(outlier_ranks) > 0:
    #     print(f"  Outlier ranks: {outlier_ranks}")
    #     for rank in outlier_ranks:
    #         print(f"    Rank {rank} had a period of {rank_periods[rank]} s")
    # else:
    #     print("  No outlier ranks found.")

    func_avg_snr = np.mean(func_all_snr)
    func_avg_ptm = np.mean(func_all_ptm)
    if np.isnan(func_avg_ptm):
        func_avg_ptm = 0.0
    func_avg_std = np.mean(func_all_std)

    function_analysis[target_function] = [func_avg_snr, func_avg_ptm, func_avg_std]

    # average_period_without_outliers = sum_periods_without_outliers / (n_procs - len(outlier_ranks))
    print(f"  SNR = {func_avg_snr} || PTM = {func_avg_ptm} || STD = {func_avg_std}")
    # print(f"  Average period for {target_function} (excluding any outliers): {average_period_without_outliers}\n")

    if "MPI" in target_function:
        plt.figure()
        plt.plot(freq, np.abs(X), label=f"Rank {int(target_function.split(' Rank ')[-1])} calculated freq: {peak_freq:.2f} Hz, period: {peak_T:.5f} s")
        # color = calc_plot[0].get_color()
        plt.scatter(point[0], point[1], 60, marker="o", color="black", facecolors="none", label="Peak frequency" if rank == n_procs-1 else None)

        plt.xlabel("Frequency (Hz)")
        plt.ylabel("FFT Magnitude |X(freq)|")
        plt.suptitle(f"FFT of {target_function} Calls ({metaslice.capitalize()} phase)", fontweight="bold", fontsize=15)
        plt.title(f"{num_bins} bins", style="italic")
        plt.xlim(0, 3 * max_freq)
        plt.ylim(0, 2.5 * max_mag)
        plt.legend(loc="upper right")
        plt.grid(True)
        if save:
            plt.savefig(f"{output_dir}/{n_procs}p_{n_steps}s_{target_function.replace('MPI_','').lower()}_{num_bins:.0e}bins_freq_{metaslice}.png")
        # plt.show()
        plt.close()

# ----------------------------------------------------------------------------------------------------------------------
# Basic analysis

print("\n-----------------------------------------------------------------------------------------------------------\n")

all_func_avg_snr = np.mean([elt[0] for elt in list(function_analysis.values())])
all_func_avg_ptm = np.mean([elt[1] for elt in list(function_analysis.values())])
all_func_avg_std = np.mean([elt[2] for elt in list(function_analysis.values())])

print(f"Universal Average SNR: {all_func_avg_snr}")
print(f"Universal Average PTM: {all_func_avg_ptm}")
print(f"Universal Average STD: {all_func_avg_std}")
print()

high_snrs, high_ptms, high_stds = [], [], []

for function in pruned_functions:
    if function in function_analysis and function_analysis[function][1] > all_func_avg_ptm:
        high_ptms.append(function)

# print(f"Functions with above-average SNR: {high_snrs}\n")
# print(f"Functions with above-average PTM: {high_ptms}\n")
# print(f"Functions with above-average STD: {high_stds}\n")

periodic_functions = high_ptms

print(f"\nFound {len(periodic_functions)} periodic functions.")

# ----------------------------------------------------------------------------------------------------------------------

periodic_function_periods = {}
for periodic_function in periodic_functions:
    # print("periodic function:  ", periodic_function)
    periodic_function_periods[periodic_function] = int(all_periods[periodic_function] * 100000.0) / 100000.0

print(f"Average period is {np.mean(list(periodic_function_periods.values()))}")
print(f"Mode period is {mode(list(periodic_function_periods.values()))[0]}")

for function, period in periodic_function_periods.items():
    print(f"  {function}: {period}")

period = mode(list(periodic_function_periods.values()))[0]
selected_functions = [function for function in periodic_functions if isclose(periodic_function_periods[function], period, rel_tol=0.001)]

print(f"\nThe selected period is {period}.\nThe selected functions are {selected_functions}.")


######################################################################################################################
#################                                                                                    #################
#################                                 METASLICE ANALYSIS                                 #################
#################                                                                                    #################
######################################################################################################################
# --------------------------------------------------------------------------------------------------------------------
# Now that we know the period of one iteration, we can find meta slices based on whether or not the period is present.
#
# For example:
#   1 - Initialization (period is not present)
#   2 - Solving Loop   (period is present)
#   3 - Finalization   (period is no longer present)
# --------------------------------------------------------------------------------------------------------------------


print("\n------------------------------------------ META-SLICE IDENTIFICATION ------------------------------------------\n")

best_start = 0.
best_end = 0.
best_count = 0.

# Perform the analysis 50 times at different starting points
num_starting_points = 5
for i in range(num_starting_points):
    starting_point = program_min_time + (i * period / num_starting_points)
    print(f"Starting at {starting_point}")

    all_loop_counts = []
    all_loop_starts = []
    all_loop_ends = []

    all_macro_periods = []
    all_macro_starts = []
    all_macro_ends = []

    # Loop through each rank
    for periodic_function in selected_functions:

        # print(f"Finding meta slices for {periodic_function}\n")

        macro_loop_counts = []
        macro_loop_ends = []
        macro_loop_starts = []

        timesteps = np.arange(starting_point, program_max_time, period)

        # Find the number of counts within some arbitrary time step, 2/3 of the way through the program
        calibrating_step = timesteps[int(len(timesteps) - (len(timesteps) / 3))]
        # print(f"{calibrating_step - period} <= {calibrating_step} < {calibrating_step + period}")
        calibrating_count = sum(1 for time in all_times[periodic_function] if (calibrating_step - period) <= calibrating_step < calibrating_step + period)
        plus_minus = int(0.001 * calibrating_count)
        # print(f"Calibrating count for {periodic_function} at time {calibrating_step} is {calibrating_count}. Setting p/m to {plus_minus}.")


        old_count = 0
        old_loop_counter = 0
        in_loop = False
        loop_counter = 0
        loop_condition = 5 # number of consecutive identical timesteps required to consider it a loop
        loop_starts = []
        loop_ends = []
        longest_loop = [0.0, 0.0, 0] # [start, stop, count]
        for i in range(timesteps.size):

            if i == 0:
                continue

            previous_timestep = timesteps[i - 1]
            current_timestep = timesteps[i]
            new_count = sum(1 for time in all_times[periodic_function] if previous_timestep <= time < current_timestep)

            if old_count - plus_minus <= new_count <= old_count + plus_minus:
                loop_counter += 1
                # Arbitrary condition to determine if we're in the loop
                if loop_counter == loop_condition and not in_loop:
                    in_loop = True
                    # print(f"  Entering loop at {timesteps[i - (loop_condition)]}")
                    loop_start = timesteps[i - (loop_condition)]
                    loop_starts.append(loop_start)
                elif in_loop and  loop_counter > longest_loop[2]:
                    longest_loop[0] = loop_start
                    longest_loop[1] = program_max_time # default val (will update if the loop during the run)
                    longest_loop[2] = loop_counter
            elif in_loop:
                # print(f"    Exiting the loop at time {current_timestep} (new count is {new_count} and old count was {old_count})\n")
                in_loop = False
                loop_end = current_timestep
                loop_ends.append(loop_end)

                if loop_start in longest_loop:
                    longest_loop[1] = loop_end

                # Means there may be some macro-level structure
                if loop_counter == old_loop_counter:
                    macro_loop_counts.append(loop_counter)
                    macro_loop_ends.append(loop_end)
                    macro_loop_starts.append(loop_start)

                loop_counter = 0

            old_loop_counter = loop_counter
            old_count = new_count

        all_loop_counts.append(longest_loop[2])
        all_loop_starts.append(longest_loop[0])
        all_loop_ends.append(longest_loop[1])

        num_macro_slices = len(macro_loop_counts)
        function_macro_slices = num_macro_slices > 0

        if function_macro_slices:
            macro_period = np.mean(np.array(macro_loop_ends) - np.array(macro_loop_starts))
            all_macro_periods.append(macro_period)
            all_macro_starts.append(macro_loop_starts[0])
            all_macro_ends.append(macro_loop_ends[-1])

        # print()
        # print(f"  The program began at 0.0s. Loops began at times {loop_starts} and ended at times {loop_ends}. The program completed at {program_max_time}s.\n")
        # print(f"  The longest loop began at time {longest_loop[0]} and lasted {longest_loop[2]} periods (until {longest_loop[1]}).")
        # print(f"  {num_macro_slices} macro slices found.")
        # if function_macro_slices:
        #     print(f"    Time between macro slices: {macro_period}")
        #     print(f"    First macro slice began at {macro_loop_starts[0]}, and the last macro slice ended at {macro_loop_ends[-1]}.")
    #     print(f"  Found {len(loop_starts)} loops total.")
    #     print()

    # print(f"\nnum loops: {all_loop_counts}")
    # print(f"\nloop starts: {all_loop_starts}")
    # print(f"\nloop ends: {all_loop_ends}")

    avg_num_loops = mode(all_loop_counts)[0]
    avg_loop_start = mode(all_loop_starts)[0]
    avg_loop_end = mode(all_loop_ends)[0]

    num_loops = int((avg_loop_end - avg_loop_start) / period)

    if num_loops > best_count:
        best_count = num_loops
        best_start = avg_loop_start
        best_end = avg_loop_end

    macro_slices = len(all_macro_periods) > 0
    if macro_slices:
        avg_macro_period = np.mean(all_macro_periods)
        avg_macro_start = np.mean(all_macro_starts)
        avg_macro_end = np.mean(all_macro_ends)

    # print(f"Period: {period}")
    # print(f"The average number of iterations found among all periodic functions is {avg_num_loops}.")
    # if macro_slices:
    #     print(f"There are {(avg_macro_end - avg_macro_start) // avg_macro_period} macro-loops.")
    print(f"  On average, the loop phase begins at {avg_loop_start} and ends at {avg_loop_end}\n-----\n")


print("\n---------------------------------------------------------------------------------------------------------------\n")
print(f"The best start is {best_start} and the best end is {best_end}, with {best_count} iterations.")

######################################################################################################################
#################                                                                                    #################
#################                                 GENERATE TIME PLOT                                 #################
#################                                                                                    #################
######################################################################################################################


# Initialize info
if plot_all_functions:
    functions_to_plot = all_functions
elif plot_filtered_functions:
    functions_to_plot = pruned_functions
else:
    functions_to_plot = selected_functions
reverse = True if sorting_key == "duration" else False
functions_to_plot = sorted(functions_to_plot, reverse=reverse, key=lambda func: sort_functions(func, sorting_dict, sorting_key)) if sorting_key is not None else functions_to_plot
# print(f"\nTop Ten Functons:\n{functions_to_plot[:10]}")
# print(f"\n'Mini-EM' is at {functions_to_plot.index('Mini-EM')}")
# print(f"\n'Mini-EM: Total Time' is at {functions_to_plot.index('Mini-EM: Total Time')}")
increment = 1.0 / len(functions_to_plot)
if output_proc != -1:
  increment *= n_procs
target_function_labels = []
target_increments = []

# Initialize grey color map for background ranks
background_colors = colormaps["Greys_r"](np.linspace(0, 1, n_procs + 1))

# Generate plots
plt.figure()
colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
iter = 1
mini_em_iter = 0
plotted_ranks = {r: {"rank_iter": 0, "mpi_iter": 0, "kokkos_iter": 0, "collective_iter": 0} for r in ranks_list}

# global_data = [[],[],[]]
path = 0
paths = []

# Loop through all functions called by the current rank
for function in functions_to_plot:

    current_increment = iter * increment
    rank = int(function.split("Rank ")[-1])

    # Create the red lines to demonstrate path
    path_number = int(function.split(" Path ")[1].split(" ")[0])
    if path_number > path:
        paths.append(current_increment)
        path = path_number

    if output_proc == -1 or rank == output_proc:

        # Get the data for the current function at the current rank
        times_list = all_times[function]
        x_data = np.array(times_list)

        # Plot at arbitrary y-value
        y_data = np.zeros_like(x_data) + current_increment
        size = [10] * len(times_list)

        # allreduces = np.zeros_like(x_data) if "MPI_Allreduce" not in function else np.ones(x_data.shape)

        # allreduce_weight = 20 if "MPI_Allreduce" in function else 1
        # for _ in range(allreduce_weight):
        #     global_data[0].extend(x_data.tolist())
        #     global_data[1].extend(y_data.tolist())
        #     global_data[2].extend(allreduces.tolist())


        # Determine if this is the target rank (and if so, color the datapoints)
        if plot_all_functions or plot_filtered_functions:

            # if function.split(" Path ")[0] in all_collectives:
            #         label = f"Rank {rank} Collective MPI Call" if plotted_ranks[rank]["collective_iter"] == 0 else None
            #         color = colors[rank]
            #         alpha = 1.0
            #         plotted_ranks[rank]["collective_iter"] += 1

            # else:
            #     label = f"Rank {rank} Call" if plotted_ranks[rank]["rank_iter"] == 0 else None
            #     color = background_colors[rank]
            #     alpha = 0.7
            #     plotted_ranks[rank]["rank_iter"] += 1

            # if function.startswith("Mini-EM: Advance Time Step"):
            #     label = "Mini-EM: Advance Time Step" if mini_em_iter == 0 else None
            #     mini_em_iter += 1
            #     alpha = 1.0
            #     color = "purple"

            mpi = True if "MPI_" in function else False
            if mpi:
                if function.split(" Path ")[0] in all_collectives:
                    label = None
                    color = colors[2] if output_proc != -1 else adjust_lightness(colors[rank], amount = 0.75)
                    alpha=1.0
                    # plotted_ranks[rank]["collective_iter"] += 1
                else:
                    label = f"Rank {rank}" if plotted_ranks[rank]["rank_iter"] == 0 else None
                    plotted_ranks[rank]["rank_iter"] += 1
                    color = colors[0] if output_proc != -1 else colors[rank]
                    alpha=1.0
                    # plotted_ranks[rank]["mpi_iter"] += 1
            else:
                label = None
                color = colors[1] if output_proc != -1 else adjust_lightness(colors[rank], amount = 1.5)
                alpha=1.0
                # plotted_ranks[rank]["kokkos_iter"] += 1

            if function.startswith("Mini-EM: Advance Time Step"):
                label = "Mini-EM: Advance Time Step" if mini_em_iter == 0 else None
                mini_em_iter += 1
                color = "purple"
                alpha=1.0

        else:
            # Create y-axis labels
            if function not in target_function_labels:
                target_function_labels.append(function)
                target_increments.append(current_increment)

            # Then create the plot
            label = f"Rank {rank}" if plotted_ranks[rank]["rank_iter"] == 0 else None
            plotted_ranks[rank]["rank_iter"] += 1
            color = colors[rank]
            alpha = 1.0

        # Create time plots
        if vertical_plot:
            plt.scatter(y_data, x_data, size, color=color, alpha=alpha, label=label)
        else:
            plt.scatter(x_data, y_data, size, color=color, alpha=alpha, label=label)

        # Update iter so rank label only prints once and y-vals are different
        iter += 1

# df = pd.DataFrame()
# df["time"] = global_data[0]
# df["depth"] = global_data[1]
# df["allreduce"] = global_data[2]
# df.to_csv(f"{app_abr}_data.csv", header=False, index=False)

# Create explainer label
target_function_labels = [label.split(" Path ")[0] for label in target_function_labels]

# Format legend box
if vertical_plot:
    plt.legend(loc="lower right")
    plt.xlim(0 - (2 * increment),(1 + (2 * increment)))
    plt.ylim(program_max_time + 1., -1.)
    plt.xticks(target_increments, target_function_labels)
    plt.xticks(rotation=65)
    plt.ylabel("Time (s)")
else:
    ax = plt.gca()
    num_labels = len(ax.get_legend_handles_labels()[1])
    # box = ax.get_position()
    # ax.set_position([box.x0, box.y0 + box.height * 0.1,
    #                 box.width, box.height * 0.9])
    # ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
    #           fancybox=True, shadow=True, ncol=num_labels // 3)
    plt.legend(loc="upper right", ncols=2, title="Dark: Collective Call\nMedium: Standard MPI Call\nLight: Kokkos Call\n")
    plt.xlim(program_min_time, program_max_time)
    plt.ylim(0,(1 + (2 * increment)))
    plt.yticks(target_increments, target_function_labels)
    plt.xlabel("Time (s)")
    plt.ylabel(yaxis_label)

# Draw the path lines
for path_height in paths:
    plt.plot([program_min_time, program_max_time], [path_height, path_height], color="purple", alpha=0.5)

# Add timestep divisions if requested
if draw_timesteps:
    num_drawn_steps = 0
    for timestep in np.arange(best_start, best_end, period):
        if timestep == best_end:
            continue
        plt.plot([timestep, timestep],[0., 1.], color="black", alpha=0.5)
        num_drawn_steps += 1
    print(f"Plotted {num_drawn_steps - 1} time steps.") # subtract one because it draws a line at the end of the last time step
    caption = f"Found {num_drawn_steps - 1} iterations with a period of {period:.4f} s\nThe start and end of each loop is shown with a black line.\nEach new level in the path is shown with a purple line."
    t = plt.figtext(0.15, 0.82, caption, wrap=True, horizontalalignment="left", fontsize=10)
    t.set_bbox(dict(facecolor="white", alpha=0.5, linewidth=0))
if draw_macroloops and macro_slices:
    for timestep in np.arange(avg_macro_start, avg_macro_end, avg_macro_period):
        plt.plot([timestep, timestep],[0., 1.], color="blue")

# Format titles
output_proc_string = f"{n_procs} Ranks" if output_proc == -1 else f"Rank {output_proc}"
plt.suptitle(f"{app} Calls Over Time ({metaslice.capitalize()} phase)", fontweight="bold", fontsize=15)
plt.title(f"{output_proc_string}, {n_steps} Timesteps", style="italic")

# Output the plot
if save:
    plt.savefig(f"{output_dir}/{n_procs}p_{n_steps}s_{metaslice}.png")
plt.show()
plt.close()
