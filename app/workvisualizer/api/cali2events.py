#
# ************************************************************************
#
# Copyright (c) 2024, NexGen Analytics, LC.
#
# WorkVisualizer is licensed under BSD-3-Clause terms of use:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ************************************************************************
#

# This file was modified by NGA from a source file in the Caliper repo (license below):

# Copyright (c) 2022, Lawrence Livermore National Security, LLC.
# See top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

# Copyright (c) 2015-2023, Lawrence Livermore National Security, LLC.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Convert a .cali trace to Google TraceEvent JSON

###################################################################################
from logging_utils.logging_utils import log_timed

import caliperreader

import json
import numpy as np
import time
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'caliper-reader'))


all_collectives = ["MPI_Allgather", "MPI_Allgatherv", "MPI_Allreduce", "MPI_Alltoall",
                   "MPI_Alltoallv", "MPI_Alltoallw", "MPI_Barrier", "MPI_Bcast",
                   "MPI_Gather", "MPI_Gatherv", "MPI_Iallgather", "MPI_Iallreduce",
                   "MPI_Ibarrier", "MPI_Ibcast", "MPI_Igather", "MPI_Igatherv",
                   "MPI_Ireduce", "MPI_Iscatter", "MPI_Iscatterv", "MPI_Reduce",
                   "MPI_Scatter", "MPI_Scatterv", "MPI_Exscan", "MPI_Op_create",
                   "MPI_Op_free", "MPI_Reduce_local", "MPI_Reduce_scatter", "MPI_Scan",
                   "MPI_User_function"]

counts_template_dict = {"kokkos": {"total_count": 0, "unique_count": 0, "time": 0.0},
                        "mpi": {"total_count": 0, "unique_count": 0, "time": 0.0},
                        "collective": {"total_count": 0, "unique_count": 0, "time": 0.0},
                        "other": {"total_count": 0, "unique_count": 0, "time": 0.0}}


def _get_first_from_list(rec, attribute_list, fallback=0):
    for attr in attribute_list:
        if attr in rec:
            return rec[attr]
    return fallback


def _get_timestamp(rec):
    """Get timestamp from rec and convert to seconds"""

    timestamp_attributes = {
        "cupti.timestamp": 1e-9,
        "rocm.host.timestamp": 1e-9,
        "time.offset.ns": 1e-9,
        "time.offset": 1e-6,
        "gputrace.timestamp": 1e-9,
        "cupti.activity.start": 1e-9,
        "rocm.starttime": 1e-9
    }

    for attr, factor in timestamp_attributes.items():
        if attr in rec:
            return float(rec[attr]) * factor

    return None


def _parse_counter_spec(spec):
    """Parse spec strings in the form
        "group=counter1,counter2,..."
    and return a string->map of strings dict
    """
    res = {}

    if spec is None:
        return res

    pos = spec.find('=')
    grp = spec[:pos] if pos > 0 else "counter"
    ctr = spec[pos + 1:] if pos > 0 else spec

    res[grp] = ctr.split(",")

    return res


class StackFrames:
    """Helper class to build the stackframe dictionary reasonably efficiently"""

    class Node:
        def __init__(self, tree, name, category, parent=None):
            self.parent = parent
            self.name = name
            self.category = category
            self.children = {}
            self.id = len(tree.nodes)
            tree.nodes.append(self)

    def __init__(self):
        self.nodes = []
        self.roots = {}

    def get_stackframe_id(self, path, category):
        if not isinstance(path, list):
            path = [path]

        name = path[0]
        key = (category, name)
        if key not in self.roots:
            self.roots[key] = StackFrames.Node(self, name, category)

        node = self.roots[key]
        for name in path[1:]:
            key = (category, name)
            if key not in node.children:
                node.children[key] = StackFrames.Node(self, name, category, node)
            node = node.children[key]

        return node.id

    def get_stackframes(self):
        result = {}

        for node in self.nodes:
            d = dict(name=node.name, category=node.category)
            if node.parent is not None:
                d["parent"] = node.parent.id
            result[node.id] = d

        return result


class CaliTraceEventConverter:
    BUILTIN_PID_ATTRIBUTES = [
        'mpi.rank',
    ]

    BUILTIN_TID_ATTRIBUTES = [
        'omp.thread.id',
        'pthread.id',
    ]

    def __init__(self, cfg, maximum_depth_limit=5):
        self.cfg = cfg

        self.records = []
        self.reader = caliperreader.CaliperStreamReader()
        self.rstack = {}

        self.stackframes = StackFrames()
        self.samples = []

        self.tsync = {}

        self.counters = self.cfg["counters"]

        self.pid_attributes = self.cfg["pid_attributes"] + self.BUILTIN_PID_ATTRIBUTES
        self.tid_attributes = self.cfg["tid_attributes"] + self.BUILTIN_TID_ATTRIBUTES

        self.skipped = 0
        self.written = 0

        # Filtering data
        self.maximum_depth_limit = maximum_depth_limit

        # These keep track of metadata
        # TODO: there must be a cleaner way to do this
        self.event_id_iterator = 0
        self.rank_event_counters = {}
        self.unique_event_counters = {}
        self.unique_functions = []
        self.known_ftns = []
        self.known_ranks = []
        self.known_depths = []
        self.rank_unique_events_dict = {}
        self.unique_events_dict = {}
        self.max_depth = 0

    @log_timed()
    def read(self, filename_or_stream):
        self.reader.read(filename_or_stream, self._process_record)

    @log_timed()
    def read_and_sort(self, filename_or_stream):
        trace = []

        def insert_into_trace(rec):
            ts = _get_timestamp(rec)
            if ts is None:
                return
            trace.append((ts, rec))

        ts = self.start_timing("  Reading ......")
        self.reader.read(filename_or_stream, insert_into_trace)
        self.end_timing(ts)

        ts = self.start_timing("  Sorting ......")
        trace.sort(key=lambda e: e[0])
        self.end_timing(ts)

        ts = self.start_timing("  Processing ...")
        for rec in trace:
            self._process_record(rec[1])
        self.end_timing(ts)

    @log_timed()
    def write(self, files_dir):

        depth_desc = "depth_full" if self.maximum_depth_limit is None else f"depth_{self.maximum_depth_limit}"
        event_output_files = {rank: os.path.join(files_dir, "events", f"events-{rank}-{depth_desc}.json") for rank in
                              self.known_ranks}
        unique_events_output_files = {
            rank: os.path.join(files_dir, "unique-events", f"unique-events-{rank}-{depth_desc}.json") for rank in
            self.known_ranks}
        metadata_output_file = os.path.join(files_dir, "metadata", f"metadata-{depth_desc}.json")
        unique_events_output_file = os.path.join(files_dir, "unique-events", f"unique-events-all-{depth_desc}.json")

        # if len(self.stackframes.nodes) > 0:
        #     result["stackFrames"] = self.stackframes.get_stackframes()
        # if len(self.samples) > 0:
        #     result["samples"] = self.samples

        events_result = sorted(self.records, key=lambda event: event["ts"])
        # Separate into rank specific lists
        events_per_rank = {rank: [] for rank in self.known_ranks}
        for event in events_result:
            events_per_rank[event["rank"]].append(event)
        # TODO: look in every rank for biggest events (not just 0)
        biggest_events = sorted(list(self.unique_events_dict.values()), key=lambda event: event["dur"], reverse=True)[
                         :10]
        metadata_result = self.reader.globals
        metadata_result["known.ranks"] = self.known_ranks
        metadata_result["known.depths"] = self.known_depths
        metadata_result["maximum.depth"] = max(self.known_depths)
        metadata_result["unique.counts"] = {}
        metadata_result["total.counts"] = {}
        agg_counts = {"total_count": {}, "unique_count": {}, "time": {}}
        for rank in self.known_ranks:
            metadata_result["unique.counts"][f"rank.{rank}"] = {
                "kokkos": self.rank_event_counters[rank]["kokkos"]["unique_count"],
                "mpi_p2p": self.rank_event_counters[rank]["mpi"]["unique_count"],
                "mpi_collective": self.rank_event_counters[rank]["collective"]["unique_count"],
                "other": self.rank_event_counters[rank]["other"]["unique_count"]}
            metadata_result["total.counts"][f"rank.{rank}"] = {
                "kokkos": self.rank_event_counters[rank]["kokkos"]["total_count"],
                "mpi_p2p": self.rank_event_counters[rank]["mpi"]["total_count"],
                "mpi_collective": self.rank_event_counters[rank]["collective"]["total_count"],
                "other": self.rank_event_counters[rank]["other"]["total_count"]}
            for call_type in self.rank_event_counters[rank].keys():
                for key, val in self.rank_event_counters[rank][call_type].items():
                    if call_type not in agg_counts[key]:
                        agg_counts[key][call_type] = val
                    else:
                        agg_counts[key][call_type] += val

        # avg_unique_counts = {"average": {key: val/len(self.known_ranks) for key, val in agg_counts["unique_count"].items()}}
        avg_total_counts = {
            "average": {key: val / len(self.known_ranks) for key, val in agg_counts["total_count"].items()}}

        metadata_result["unique.counts"].update({"global": self.unique_event_counters})
        metadata_result["total.counts"].update(avg_total_counts)
        program_runtime = events_result[-1]["ts"] + events_result[-1]["dur"] - events_result[0]["ts"]
        metadata_result["program.runtime"] = program_runtime
        metadata_result["biggest.calls"] = biggest_events
        metadata_result["imbalance"] = []

        indent = 4 if self.cfg["pretty_print"] else None

        # Look for outlier ranks in the unique events
        for event in self.unique_events_dict.values():
            ftn_id = event["ftn_id"]
            all_rank_times = {rank: rank_info["dur"] for rank, rank_info in event["rank_info"].items()}
            average_time = np.mean(list(all_rank_times.values()))
            std_dev = np.std(list(all_rank_times.values()))
            diffs = []
            for rank, time in all_rank_times.items():

                if time > average_time + (1.5 * std_dev):  # This one will yield some imbalance (good for testing)
                    # if np.abs(average_time - time) > 2 * std_dev:   # This one is probably a better metric, but on ExaMiniMD will not yield any imbalance

                    # Calculate percent difference
                    pct_diff = (time - average_time) / average_time

                    if "imbalance" not in self.unique_events_dict[ftn_id]:
                        self.unique_events_dict[ftn_id]["imbalance"] = []
                    self.unique_events_dict[ftn_id]["imbalance"].append({rank: pct_diff})

                    self.rank_unique_events_dict[rank][ftn_id]["imbalance"] = pct_diff
                    diffs.append(pct_diff)

            # TODO: Improve metric for imbalance here (this is only recording pct_diff for one rank)
            if len(diffs) > 0:
                metadata_result["imbalance"].append(
                    {"name": event["name"], "ftn_id": ftn_id, "imbalance": sum(diffs) / len(diffs)})

        for rank in self.known_ranks:
            with open(event_output_files[rank], "w") as event_output:
                json.dump(events_per_rank[rank], event_output, indent=indent)
            with open(unique_events_output_files[rank], "w") as unique_events_output:
                json.dump(sorted(list((self.rank_unique_events_dict[rank].values())), key=lambda e: e["depth"]),
                          unique_events_output, indent=indent)
        with open(unique_events_output_file, "w") as unique_events_output_all:
            json.dump(sorted(list((self.unique_events_dict.values())), key=lambda e: e["depth"]),
                      unique_events_output_all, indent=indent)
        with open(metadata_output_file, "w") as metadata_output:
            json.dump(metadata_result, metadata_output, indent=indent)

        self.written += len(self.records) + len(self.samples)

    @log_timed()
    def sync_timestamps(self):
        if len(self.tsync) == 0:
            return

        maxts = max(self.tsync.values())
        adjust = {pid: maxts - ts for pid, ts in self.tsync.items()}

        for rec in self.records:
            rec["ts"] += adjust.get(rec["pid"], 0.0)
        for rec in self.samples:
            rec["ts"] += adjust.get(rec["pid"], 0.0)

    def start_timing(self, name):
        if self.cfg["verbose"]:
            print(name, file=sys.stderr, end='', flush=True)

        return time.perf_counter()

    def end_timing(self, begin):
        end = time.perf_counter()
        tot = end - begin

        if self.cfg["verbose"]:
            print(f" done ({tot:.2f}s).", file=sys.stderr)

    def _get_type(self, function_name):
        if "MPI_" in function_name:
            if function_name in all_collectives:
                return "collective"
            else:
                return "mpi"
        elif "Kokkos::" in function_name:
            return "kokkos"
        else:
            return "other"

    def filter_rec(self, key, rec):
        keys = list(rec.keys())
        kernel_type_filter = "kernel_type" in keys and "kokkos.fence" in rec["kernel_type"]
        depth_filter = key.startswith("event.begin#") and len(rec.get("path", [])) >= int(self.maximum_depth_limit) or \
                       key.startswith("event.end#") and len(rec.get("path", [])) - 1 >= int(self.maximum_depth_limit)

        if key.startswith("event.begin#"):
            depth = len(rec.get("path", []))
            if depth not in self.known_depths and depth > 0:
                self.known_depths.append(depth)

        return kernel_type_filter or depth_filter

    def _process_record(self, rec):
        pid = int(_get_first_from_list(rec, self.pid_attributes))
        tid = int(_get_first_from_list(rec, self.tid_attributes))

        trec = dict(pid=pid, tid=tid)

        self._process_counters(rec, (pid, tid))

        if "cupti.activity.kind" in rec:
            self._process_cupti_activity_rec(rec, trec)
        elif "rocm.activity" in rec:
            self._process_roctracer_activity_rec(rec, trec)
        elif "umpire.alloc.name" in rec:
            self._process_umpire_rec(rec, trec)
        elif "source.function#cali.sampler.pc" in rec:
            self._process_sample_rec(rec, trec)
            return
        elif "gputrace.begin" in rec:
            self._process_gputrace_begin(rec, pid)
            return
        elif "gputrace.end" in rec:
            self._process_gputrace_end(rec, pid, trec)
        elif "ts.sync" in rec:
            self._process_timesync_rec(rec, pid)
            return
        else:
            keys = list(rec.keys())
            for key in keys:
                if self.filter_rec(key, rec):
                    continue
                if key.startswith("event.begin#"):
                    self._process_event_begin_rec(rec, (pid, tid), key)
                    return
                if key.startswith("event.end#"):
                    self._process_event_end_rec(rec, (pid, tid), key, trec)
                    break
                else:
                    self.skipped += 1

        if "name" in trec:
            self.records.append(trec)

    def _process_gputrace_begin(self, rec, pid):
        block = rec.get("gputrace.block")
        skey = ((pid, int(block)), "gputrace")
        tst = float(rec["gputrace.timestamp"]) * 1e-3

        if skey in self.rstack:
            self.rstack[skey].append(tst)
        else:
            self.rstack[skey] = [tst]

    def _process_gputrace_end(self, rec, pid, trec):
        block = rec.get("gputrace.block")
        skey = ((pid, int(block)), "gputrace")
        btst = self.rstack[skey].pop()
        tst = float(rec["gputrace.timestamp"]) * 1e-3

        name = rec.get("gputrace.region")
        if isinstance(name, list):
            name = name[-1]

        trec.update(ph="X", name=name, cat="gpu", ts=btst, dur=(tst - btst), tid="block." + str(block))

    def _process_timesync_rec(self, rec, pid):
        self.tsync[pid] = _get_timestamp(rec)

    def _process_event_begin_rec(self, rec, loc, key):
        attr = key[len("event.begin#"):]
        tst = _get_timestamp(rec)

        raw_path = rec.get("path", [])
        raw_kernel_type = rec.get("kernel_type", [])
        path = "/".join(raw_path) if isinstance(raw_path, list) and len(raw_path) > 0 else ""
        kernel_type = "/".join(raw_kernel_type) if isinstance(raw_kernel_type, list) and len(
            raw_kernel_type) > 0 else ""

        eid = self.event_id_iterator
        self.event_id_iterator += 1

        identifier = f"{rec[key]} {path}"
        if identifier not in self.known_ftns:
            self.known_ftns.append(identifier)
            ftn_id = self.known_ftns.index(identifier)
        else:
            ftn_id = self.known_ftns.index(identifier)

        depth = len(raw_path)

        if depth > self.max_depth:
            self.max_depth = depth

        rank = int(rec.get("mpi.rank"))
        if rank not in self.known_ranks:
            self.known_ranks.append(rank)
            self.rank_event_counters[rank] = counts_template_dict

        skey = (loc, attr)

        if skey in self.rstack:
            self.rstack[skey].append((tst, path, kernel_type, rank, eid, ftn_id, depth))
        else:
            self.rstack[skey] = [(tst, path, kernel_type, rank, eid, ftn_id, depth)]

    def _process_event_end_rec(self, rec, loc, key, trec):
        attr = key[len("event.end#"):]
        btst, path, kernel_type, rank, eid, ftn_id, depth = self.rstack[(loc, attr)].pop()
        tst = _get_timestamp(rec)
        dur = tst - btst
        name = rec[key]

        self._get_stackframe(rec, trec)

        type = self._get_type(name)

        self.rank_event_counters[rank][type]["time"] += (tst - btst)
        self.rank_event_counters[rank][type]["total_count"] += 1

        # Removed from trec: {ph="X", cat=attr}
        trec.update(name=name, eid=eid, ftn_id=ftn_id, depth=depth, type=type, ts=btst, dur=dur, path=path,
                    kernel_type=kernel_type, rank=rank)

        if name not in self.unique_functions:
            self.rank_event_counters[rank][type]["unique_count"] += 1
            self.unique_functions.append(name)
            if type not in self.unique_event_counters:
                self.unique_event_counters[type] = 1
            else:
                self.unique_event_counters[type] += 1

        if ftn_id not in self.unique_events_dict:
            self.unique_events_dict[ftn_id] = trec.copy()
            self.unique_events_dict[ftn_id]["count"] = 1
            self.unique_events_dict[ftn_id]["rank_info"] = {rank: {"count": 1, "dur": dur}}
            del self.unique_events_dict[ftn_id]["rank"]
            del self.unique_events_dict[ftn_id]["eid"]
        else:
            self.unique_events_dict[ftn_id]["dur"] += dur
            self.unique_events_dict[ftn_id]["count"] += 1
            if rank not in self.unique_events_dict[ftn_id]["rank_info"]:
                self.unique_events_dict[ftn_id]["rank_info"][rank] = {"count": 1, "dur": dur}
            else:
                self.unique_events_dict[ftn_id]["rank_info"][rank]["count"] += 1
                self.unique_events_dict[ftn_id]["rank_info"][rank]["dur"] += dur

        if rank not in self.rank_unique_events_dict:
            self.rank_unique_events_dict[rank] = {}

        if ftn_id not in self.rank_unique_events_dict[rank]:
            self.rank_unique_events_dict[rank][ftn_id] = trec.copy()
            self.rank_unique_events_dict[rank][ftn_id]["count"] = 1
            del self.rank_unique_events_dict[rank][ftn_id]["rank"]
            del self.rank_unique_events_dict[rank][ftn_id]["eid"]
        else:
            self.rank_unique_events_dict[rank][ftn_id]["dur"] += dur
            self.rank_unique_events_dict[rank][ftn_id]["count"] += 1

    def _process_cupti_activity_rec(self, rec, trec):
        cat = rec["cupti.activity.kind"]
        tst = float(rec["cupti.activity.start"]) * 1e-3
        dur = float(rec["cupti.activity.duration"]) * 1e-3
        name = rec.get("cupti.kernel.name", cat)

        trec.update(ph="X", name=name, cat=cat, ts=tst, dur=dur, tid="cuda")

    def _process_roctracer_activity_rec(self, rec, trec):
        cat = rec["rocm.activity"]
        tst = float(rec["rocm.starttime"]) * 1e-3
        dur = float(rec["rocm.activity.duration"]) * 1e-3
        name = rec.get("rocm.kernel.name", cat)

        trec.update(ph="X", name=name, cat=cat, ts=tst, dur=dur, tid="rocm")

    def _process_sample_rec(self, rec, trec):
        trec.update(name="sampler", weight=1, ts=_get_timestamp(rec))

        if "cpuinfo.cpu" in rec:
            trec.update(cpu=rec["cpuinfo.cpu"])

        self._get_stackframe(rec, trec)
        self.samples.append(trec)

    def _process_counters(self, rec, loc):
        for grp, counters in self.counters.items():
            args = {}
            for counter in counters:
                if counter in rec:
                    args[counter] = float(rec[counter])
            if len(args) > 0:
                ts = _get_timestamp(rec)
                trec = dict(ph="C", name=grp, pid=loc[0], tid=loc[1], ts=ts, args=args)
                self.records.append(trec)

    def _process_umpire_rec(self, rec, trec):
        name = "Alloc " + rec["umpire.alloc.name"]
        size = float(rec["umpire.alloc.current.size"])
        hwm = float(rec["umpire.alloc.highwatermark"])
        tst = _get_timestamp(rec)
        args = {"size": size}

        trec.update(ph="C", name=name, ts=tst, args=args)

    def _get_stackframe(self, rec, trec):
        key = "source.function#callpath.address"
        if key in rec:
            sf = self.stackframes.get_stackframe_id(rec[key], "callstack")
            trec.update(sf=sf)


@log_timed()
def convert_cali_to_json(input_files: list, files_dir: str, maximum_depth_limit: int = 5):
    cfg = {
        "pretty_print": True,
        "sync_timestamps": True,
        "counters": {},
        "tid_attributes": [],
        "pid_attributes": [],
        "verbose": False
    }

    converter = CaliTraceEventConverter(cfg, maximum_depth_limit)

    begin = time.perf_counter()

    for file in input_files:
        with open(file) as input:
            converter.read_and_sort(input)

    if cfg["sync_timestamps"]:
        ts = converter.start_timing("Syncing ...")
        converter.sync_timestamps()
        converter.end_timing(ts)

    ts = converter.start_timing("Writing ...")

    events_dir = os.path.join(files_dir, "events")
    os.makedirs(events_dir, exist_ok=True)

    unique_dir = os.path.join(files_dir, "unique-events")
    os.makedirs(unique_dir, exist_ok=True)

    metadata_dir = os.path.join(files_dir, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)

    converter.write(files_dir)
    converter.end_timing(ts)

    end = time.perf_counter()
    tot = end - begin
    wrt = converter.written

    print(f"Done. {wrt} records written. Total {tot:.2f}s.", file=sys.stderr)
