import os
import json
import random
import numpy as np
import matplotlib.pyplot as plt

"""
This script produces the "events.json" equivalent of the mock hierarchy in s1_generate_hierarchy.py.
Then, it converts the JSON into a time series format, sampling the points at some regular interval.
The resulting time series is then plotted.
"""

def create_events_data(num_loops=100, anomaly=False):
    events_list = [{"name": "0",
                    "ts": 0.0,
                    "dur": 6.7}]

    initialization = [
        {"name": "1",  # 0.1 - 0.6
         "ts": 0.1,
         "dur": 0.5},
        {"name": "2",  # 0.2 - 0.4
         "ts": 0.2,
         "dur": 0.2},
        {"name": "3",  # 0.4 - 0.6
         "ts": 0.4,
         "dur": 0.2},
        {"name": "4",  # 0.7 - 1.1
         "ts": 0.7,
         "dur": 0.4},
        {"name": "5",  # 0.8 - 1.1
         "ts": 0.8,
         "dur": 0.3}
    ]

    anomalous_loop = random.randint(0, num_loops)
    anomaly_val = 0.7 if anomaly else 0.0
    solving_loop = []
    ts_6 = 1.2
    typical_loop_time = 0.0
    for i in range(num_loops):
        anomaly_injection = 0 if i != anomalous_loop else anomaly_val
        ts_7 = ts_6 + 0.1
        dur_7 = 0.3 + anomaly_injection
        ts_8 = ts_7 + dur_7
        dur_8 = 0.2 + anomaly_injection
        ts_9 = ts_8 + dur_8
        dur_9 = 0.2 + anomaly_injection
        ts_10 = ts_9 + 0.1
        dur_10 = 0.1 + anomaly_injection
        dur_6 = dur_7 + dur_8 + dur_9 + anomaly_injection
        if typical_loop_time == 0.0 and anomaly_injection == 0:
            typical_loop_time = dur_6

        current_loop = [
            {"name": "6",
             "ts": ts_6,
             "dur": dur_6},
            {"name": "7",
             "ts": ts_7,
             "dur": dur_7},
            {"name": "8",
             "ts": ts_8,
             "dur": dur_8},
            {"name": "9",
             "ts": ts_9,
             "dur": dur_9},
            {"name": "10",
             "ts": ts_10,
             "dur": dur_10},
        ]

        ts_6 += dur_6 + 0.1

        solving_loop.extend(current_loop)

    ts_11 = ts_6 + dur_6 + 0.1
    dur_11 = 0.3
    ts_12 = ts_11 + 0.1
    dur_12 = 0.2
    ts_13 = ts_11 + dur_11 + 0.1
    dur_13 = 0.2
    ts_14 = ts_13 + dur_13
    dur_14 = 0.1
    finalization = [
        {"name": "11",
         "ts": ts_11,
         "dur": dur_11},
        {"name": "12",
         "ts": ts_12,
         "dur": dur_12},
        {"name": "13",
         "ts": ts_13,
         "dur": dur_13},
        {"name": "14",
         "ts": ts_14,
         "dur": dur_14}
    ]

    events_list.extend(initialization)
    events_list.extend(solving_loop)
    events_list.extend(finalization)

    output_file = os.path.join(os.getcwd(), "mock_events.json")
    with open(output_file, "w") as out_json:
        json.dump(events_list, out_json, indent=4)

    return events_list, typical_loop_time

def create_time_series(num_samples=10000, num_loops=100, anomaly=False):
    events, typical_loop_time = create_events_data(num_loops, anomaly=anomaly)

    events_file = "/home/calebschilly/Develop/WorkVisualizer/WorkVisualizer/app/workvisualizer/api/files/events/events-0-depth_5.json"
    with open(events_file, 'r') as f:
        events = json.load(f)

    time_range = (events[0]["ts"], events[-1]["ts"] + events[-1]["dur"])
    bins = np.linspace(time_range[0], time_range[1], num_samples)

    call_data = np.zeros_like(bins)

    for i in range(len(bins) - 1):
        bin_start = bins[i]
        bin_end = bins[i+1]
        for event in events:
            if bin_start <= event["ts"] <= bin_end or event["ts"] <= bin_start <= event["ts"] + event["dur"]:
                call_data[i] += 1

    filtered_bins = bins[5000:5000+230]
    filtered_data = call_data[5000:5000+230]

    plt.figure()
    plt.plot(bins, call_data)
    plt.title("Time Series Representation")
    plt.xlabel("Bins (s)")
    plt.ylabel("Number of Calls Occurring in Step")
    # plt.plot(filtered_steps, filtered_data, c="r")
    plt.show()

    return (bins, call_data, typical_loop_time)

def main():
    time_series = create_time_series(num_loops=10)

if __name__ == "__main__":
    main()
