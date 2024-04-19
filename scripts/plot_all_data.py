"""Plots the MPI and Kokkos data over time."""


import os
import json
import argparse
import numpy as np
from math import log10, floor, isclose
from scipy.stats import mode
from scipy.signal import find_peaks
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


# Parse command line arg for the json file
parser = argparse.ArgumentParser(description="Takes in the path to an executable and returns a visualization of the Kokkos kernels.")
parser.add_argument("-i", "--input", help="Input JSON file containing MPI traces for all ranks.")
parser.add_argument("-s", "--save", action="store_true", help="Whether or not to save the plot to a file.")
parser.add_argument("-a", "--all", action="store_true", help="Whether or not to plot ALL functions on the final plot (and not just the periodic ones).")
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
n_procs = int(file_splits[1].split("p")[0])
n_steps = int(file_splits[2].split("s")[0])

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

# Get all ranks' init time
all_init_times = [0.] * n_procs
program_max_time = 0.
program_min_time = 0. # we enforce this later when dealing with the offset

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

    # Add to times dict
    if function_name not in all_times:
        all_times.setdefault(function_name, {proc: [] for proc in range(n_procs)})
    all_times[function_name][rank].append(begin_time)

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

# Correct the offset among ranks
true_time = min(all_init_times)
offsets = [init_time - true_time for init_time in all_init_times]
for function_name, rank_times in all_times.items():
    for rank, timestamps in rank_times.items():
        all_times[function_name][rank] = [timestamp - offsets[rank] - true_time for timestamp in timestamps]

# Get the data for ALL functions before filtering down
all_functions = list(all_times.keys())
all_function_counts = np.array(list(function_total_counts.values()))
all_function_names = np.array(list(function_total_counts.keys()))
max_sort_indices = np.flip(np.argsort(all_function_counts)) # to get in descending order
sorted_names = all_function_names[max_sort_indices]

# Only take functions in the top <percent>% of counts
percent = 0.10
num_pruned_functions = int(percent * len(all_function_names))
pruned_functions = sorted_names[:num_pruned_functions]

print(f"There are {len(all_functions)} total, but we filter down to the {num_pruned_functions} most frequent functions for analysis.")


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

    # Initialize the list for all periods (regardless of rank) corresponding to the function
    all_periods[target_function] = []

    # ----------------------------------------------------------------------------------------------------------------
    # BINS

    # Make sure that the function exists
    if target_function not in all_times:
        continue
    function_times_dict = all_times[target_function]

    # Determine time range
    all_target_times = np.concatenate(list(function_times_dict.values()))
    min_time = np.min(all_target_times)
    max_time = np.max(all_target_times)

    # Could mean that each processor just called it once
    if len(all_target_times) == n_procs:
        continue

    # Plot number of instances of each rank at each timestep
    binned_data = {}
    for rank in ranks_list:
        timestamps = function_times_dict[rank]
        counts, binned_times = np.histogram(timestamps, bins=num_bins)
        binned_data[rank] = [binned_times, counts]
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

    rank_periods = {}
    sum_periods = 0.
    max_freq = 0.
    max_mag = 0.

    # Protects against case where one rank is working while others aren't
    present_ranks = [rank for rank in function_times_dict.keys() if function_times_dict[rank]]
    func_all_snr, func_all_ptm, func_all_std = [], [], []
    function_analysis[target_function] = {}

    # Get period for each rank
    for rank in present_ranks:
        duration = max(function_times_dict[rank]) - min(function_times_dict[rank])

        if duration == 0:
            continue

        sr = num_bins / duration
        x = binned_data[rank][1]
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
                break  # Something has gone right
            if i > 5:
                break  # Something has gone wrong

        peak_freq = np.abs(freq[max_freq_index])
        peak_T = 1/peak_freq
        peak_mag = np.abs(X)[max_freq_index]
        point = [peak_freq, peak_mag]

        # calc_plot = plt.plot(freq, np.abs(X), label=f"Rank {rank} calculated freq: {peak_freq:.2f} Hz, period: {peak_T:.5f} s")
        # color = calc_plot[0].get_color()
        # plt.scatter(point[0], point[1], 60, marker="o", color="black", facecolors="none", label="Peak frequency" if rank == n_procs-1 else None)

        snr = signal_to_noise(np.abs(X))
        ptm = peak_mag / np.mean(np.abs(X))
        std = np.std(np.abs(X))
        if np.isnan(ptm):
            ptm = 0

        rank_periods[rank] = peak_T
        sum_periods += peak_T

        if peak_freq > max_freq:
            max_freq = peak_freq

        if peak_mag > max_mag:
            max_mag = peak_mag

        func_all_snr.append(snr)
        func_all_ptm.append(ptm)
        func_all_std.append(std)

    # Generate the FFT plot
    # plt.xlabel("Frequency (Hz)")
    # plt.ylabel("FFT Magnitude |X(freq)|")
    # plt.suptitle(f"FFT of {target_function} Calls ({metaslice.capitalize()} phase)", fontweight="bold", fontsize=15)
    # plt.title(f"{num_bins} bins", style="italic")
    # plt.xlim(0, 3 * max_freq)
    # plt.ylim(0, 2.5 * max_mag)
    # plt.legend(loc="upper right")
    # plt.grid(True)
    # if save:
    #     plt.savefig(f"{output_dir}/{n_procs}p_{n_steps}s_{target_function.replace('MPI_','').lower()}_{num_bins:.0e}bins_freq_{metaslice}.png")
    # if target_function == "MPI_Allreduce":
    # plt.show()
    # plt.close()

    # q1 = np.quantile(list(rank_periods.values()), 0.25)
    # q3 = np.quantile(list(rank_periods.values()), 0.75)
    # iqr = q3 - q1
    # # low_threshold = q1 - iqr # could check for super fast ranks
    # high_threshold = q3 + iqr
    # outlier_ranks = []
    # sum_periods_without_outliers = 0.

    for rank in present_ranks:
        if rank not in rank_periods:
            continue
        period = rank_periods[rank]
        all_periods[target_function].append(period)
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

avg_periods_per_function = []
func_period_dict = {}
for periodic_function in periodic_functions:
    # print("periodic function:  ", periodic_function)
    func_periods = []
    for time in all_periods[periodic_function]:
        # print("time: ", time)
        func_periods.append(time)
    func_period_dict[periodic_function] = np.mean(func_periods)
    avg_periods_per_function.append(np.mean(func_periods))

print(f"Average period is {np.mean(avg_periods_per_function)}")
print(f"Mode period is {mode(avg_periods_per_function)[0]}")

period = mode(avg_periods_per_function)[0]
for function, period in func_period_dict.items():
    print(f"  {function}: {period}")
selected_functions = [function for function in periodic_functions if isclose(func_period_dict[function], period, rel_tol=0.001)]

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

all_loop_counts = []
all_loop_starts = []
all_loop_ends = []

all_macro_periods = []
all_macro_starts = []
all_macro_ends = []

# Loop through each rank
for periodic_function in selected_functions:

    print(f"Finding meta slices for {periodic_function}\n")

    macro_loop_counts = []
    macro_loop_ends = []
    macro_loop_starts = []

    for rank, times in all_times[periodic_function].items():
        print(f"  Rank {rank}")
        timesteps = np.arange(program_min_time, program_max_time, period)

        old_count = 0
        old_loop_counter = 0
        in_loop = False
        loop_counter = 0
        loop_condition = 5 # number of consecutive identical timesteps required to consider it a loop
        loop_starts = []
        loop_ends = []
        plus_minus = 10 # cushion for what is considered a loop
        longest_loop = [0.0, 0.0, 0] # [start, stop, count]
        for i in range(timesteps.size):

            if i == 0:
                continue

            previous_timestep = timesteps[i - 1]
            current_timestep = timesteps[i]
            new_count = sum(1 for time in times if previous_timestep <= time < current_timestep)

            if old_count - plus_minus <= new_count <= old_count + plus_minus:
                loop_counter += 1
                # Arbitrary condition to determine if we're in the loop
                if loop_counter == loop_condition and not in_loop:
                    in_loop = True
                    print(f"  Entering loop at {timesteps[i - loop_condition]}")
                    loop_start = timesteps[i - loop_condition]
                    loop_starts.append(loop_start)
                elif in_loop:
                    if loop_counter > longest_loop[2]:
                        longest_loop[0] = loop_start
                        longest_loop[1] = program_max_time # default val (will update if the loop during the run)
                        longest_loop[2] = loop_counter
            else:
                if in_loop:
                    print(f"    Exiting the loop at time {current_timestep} (new count is {new_count} and old count was {old_count})\n")
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

    print()
    print(f"  The program began at 0.0s. Loops began at times {loop_starts} and ended at times {loop_ends}. The program completed at {program_max_time}s.\n")
    print(f"  The longest loop began at time {longest_loop[0]} and lasted {longest_loop[2]} periods (until {longest_loop[1]}).")
    print(f"  {num_macro_slices} macro slices found.")
    if function_macro_slices:
        print(f"    Time between macro slices: {macro_period}")
        print(f"    First macro slice began at {macro_loop_starts[0]}, and the last macro slice ended at {macro_loop_ends[-1]}.")
    print(f"  Found {len(loop_starts)} loops total.")
    print()

avg_num_loops = int(np.mean(all_loop_counts))
avg_loop_start = np.mean(all_loop_starts)
avg_loop_end = np.mean(all_loop_ends)

macro_slices = len(all_macro_periods) > 0
if macro_slices:
    avg_macro_period = np.mean(all_macro_periods)
    avg_macro_start = np.mean(all_macro_starts)
    avg_macro_end = np.mean(all_macro_ends)

print("\n---------------------------------------------------------------------------------------------------------------\n")
print(f"Period: {period}")
print(f"The average number of iterations found among all periodic functions is {avg_num_loops}.")
if macro_slices:
    print(f"There are {(avg_macro_end - avg_macro_start) // avg_macro_period} macro-loops.")
print(f"On average, the loop phase begins at {avg_loop_start} and ends at {avg_loop_end}\n")


######################################################################################################################
#################                                                                                    #################
#################                                 GENERATE TIME PLOT                                 #################
#################                                                                                    #################
######################################################################################################################


# Initialize info
functions_to_plot = all_functions if plot_all_functions else selected_functions
increment = 1.0 / len(functions_to_plot)
target_function_labels = []
target_increments = []

# Initialize grey color map for background ranks
background_colors = colormaps["Greys_r"](np.linspace(0, 1, n_procs + 1))

# Generate plots
plt.figure()
mpi_iter, kokkos_iter, collective_iter = 0, 0, 0
colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
for rank in ranks_list:

    # Only plot specified rank(s)
    if output_proc == -1 or rank == output_proc:
        iter = 1

        # Loop through all functions called by the current rank
        for function in functions_to_plot:
            current_increment = iter * increment

            # Get the data for the current function at the current rank
            times_list = all_times[function][rank]
            x_data = np.array(times_list)

            # Plot at arbitrary y-value
            y_data = np.zeros_like(x_data) + current_increment
            size = [10] * len(times_list)

            # Determine if this is the target rank (and if so, color the datapoints)
            if plot_all_functions:

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
            else:
                # Create y-axis labels
                if function not in target_function_labels:
                    target_function_labels.append(function)
                    target_increments.append(current_increment)

                # Then create the plot
                label = f"Rank {rank}" if iter == 1 else None
                color = colors[rank]

            # Create time plots
            if vertical_plot:
                plt.scatter(y_data, x_data, size, color=color, label=label)
            else:
                plt.scatter(x_data, y_data, size, color=color, label=label)

            # Update iter so rank label only prints once and y-vals are different
            iter += 1

    # Ignore ranks that user did not specify
    else:
      continue

# Format legend box
if vertical_plot:
    plt.legend(loc="lower right")
    plt.xlim(0 - (2 * increment),(1 + (2 * increment)))
    plt.ylim(program_max_time + 1., -1.)
    plt.xticks(target_increments, target_functions_labels)
    plt.xticks(rotation=65)
    plt.ylabel("Time (s)")
else:
    num_labels = len(plt.gca().get_legend_handles_labels()[1])
    plt.legend(loc="upper right", ncols=num_labels//3)
    plt.xlim(program_min_time, program_max_time)
    plt.ylim(0,(1 + (2 * increment)))
    plt.yticks(target_increments, target_function_labels)
    plt.xlabel("Time (s)")

# Add timestep divisions if requrested
caption = f"Found {avg_num_loops} iterations with a period of {period:.4f} s\nEach loop is represented with a black line."
if draw_timesteps:
    for timestep in np.arange(avg_loop_start, avg_loop_end, period):
        plt.plot([timestep, timestep],[0., 1.], color="black", alpha=0.5)
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
