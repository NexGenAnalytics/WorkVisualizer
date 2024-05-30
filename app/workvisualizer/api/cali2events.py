#!/usr/bin/env python3

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

# The original script has been edited

import json
import time
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'caliper-reader'))
import caliperreader

all_collectives = ["MPI_Allgather", "MPI_Allgatherv", "MPI_Allreduce", "MPI_Alltoall",
                   "MPI_Alltoallv", "MPI_Alltoallw", "MPI_Barrier", "MPI_Bcast",
                   "MPI_Gather", "MPI_Gatherv", "MPI_Iallgather", "MPI_Iallreduce",
                   "MPI_Ibarrier", "MPI_Ibcast", "MPI_Igather", "MPI_Igatherv",
                   "MPI_Ireduce", "MPI_Iscatter", "MPI_Iscatterv", "MPI_Reduce",
                   "MPI_Scatter", "MPI_Scatterv", "MPI_Exscan", "MPI_Op_create",
                   "MPI_Op_free", "MPI_Reduce_local", "MPI_Reduce_scatter", "MPI_Scan",
                   "MPI_User_function"]

counters = {"kokkos": {"total_count": 0, "unique_count": 0, "time": 0.0},
            "mpi": {"total_count": 0, "unique_count": 0, "time": 0.0},
            "collective": {"total_count": 0, "unique_count": 0, "time": 0.0},
            "other": {"total_count": 0, "unique_count": 0, "time": 0.0}}

unique_functions = []
global_hierarchy_functions = []

def _get_first_from_list(rec, attribute_list, fallback=0):
    for attr in attribute_list:
        if attr in rec:
            return rec[attr]
    return fallback

def _get_timestamp(rec):
    """Get timestamp from rec and convert to seconds"""

    timestamp_attributes = {
        "cupti.timestamp"      : 1e-9,
        "rocm.host.timestamp"  : 1e-9,
        "time.offset.ns"       : 1e-9,
        "time.offset"          : 1e-6,
        "gputrace.timestamp"   : 1e-9,
        "cupti.activity.start" : 1e-9,
        "rocm.starttime"       : 1e-9
    }

    for attr,factor in timestamp_attributes.items():
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
    grp = spec[:pos]   if pos > 0 else "counter"
    ctr = spec[pos+1:] if pos > 0 else spec

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
            path = [ path ]

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
            d = dict(name=node.name,category=node.category)
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

    def __init__(self, cfg):
        self.cfg     = cfg

        self.records = []
        self.reader  = caliperreader.CaliperStreamReader()
        self.rstack  = {}

        self.stackframes = StackFrames()
        self.samples = []

        self.tsync   = {}

        self.counters = self.cfg["counters"]

        self.pid_attributes = self.cfg["pid_attributes"] + self.BUILTIN_PID_ATTRIBUTES
        self.tid_attributes = self.cfg["tid_attributes"] + self.BUILTIN_TID_ATTRIBUTES

        self.skipped = 0
        self.written = 0

    def read(self, filename_or_stream):
        self.reader.read(filename_or_stream, self._process_record)

    def read_and_sort(self, filename_or_stream):
        trace = []

        def insert_into_trace(rec):
            ts = _get_timestamp(rec)
            if ts is None:
                return
            trace.append((ts,rec))

        ts = self.start_timing("  Reading ......")
        self.reader.read(filename_or_stream, insert_into_trace)
        self.end_timing(ts)

        ts = self.start_timing("  Sorting ......")
        trace.sort(key=lambda e : e[0])
        self.end_timing(ts)

        ts = self.start_timing("  Processing ...")
        for rec in trace:
            self._process_record(rec[1])
        self.end_timing(ts)

    def write(self, events_output, metadata_output, hierarchy_output):
        result = dict(traceEvents=self.records, otherData=self.reader.globals)

        if len(self.stackframes.nodes) > 0:
            result["stackFrames"] = self.stackframes.get_stackframes()
        if len(self.samples) > 0:
            result["samples"] = self.samples

        events_result = sorted(result["traceEvents"], key=lambda event : event["ts"])
        biggest_events = sorted(result["traceEvents"], key=lambda event : event["dur"], reverse=True)[:10]
        metadata_result = result["otherData"]
        metadata_result["unique.counts"] = {"kokkos": counters["kokkos"]["unique_count"],
                                     "mpi_p2p": counters["mpi"]["unique_count"],
                                     "mpi_collective": counters["collective"]["unique_count"],
                                     "other": counters["other"]["unique_count"]}
        metadata_result["total.counts"] = {"kokkos": counters["kokkos"]["total_count"],
                                     "mpi_p2p": counters["mpi"]["total_count"],
                                     "mpi_collective": counters["collective"]["total_count"],
                                     "other": counters["other"]["total_count"]}
        program_runtime = events_result[-1]["ts"] + events_result[-1]["dur"] - events_result[0]["ts"]
        metadata_result["program.runtime"] = program_runtime
        # metadata_result["runtime.breakdown"] = {"kernel.time": counters["kokkos"]["time"],
        #                                         "mpi_p2p.time": counters["mpi"]["time"],
        #                                         "mpi_collective.time": counters["collective"]["time"],
        #                                         "idle.time": program_runtime - counters["kokkos"]["time"] - counters["mpi"]["time"] - counters["collective"]["time"]}
        metadata_result["biggest.calls"] = [{event["name"]: event["dur"]} for event in biggest_events]
        metadata_result["hierarchy num events"] = len(global_hierarchy_functions)
        indent = 4 if self.cfg["pretty_print"] else None
        json.dump(events_result, events_output, indent=indent)
        json.dump(metadata_result, metadata_output, indent=indent)
        json.dump(global_hierarchy_functions, hierarchy_output, indent=indent)
        self.written += len(self.records) + len(self.samples)

    def sync_timestamps(self):
        if len(self.tsync) == 0:
            return

        maxts = max(self.tsync.values())
        adjust = { pid: maxts - ts for pid, ts in self.tsync.items() }

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

    def _process_record(self, rec):
        pid  = int(_get_first_from_list(rec, self.pid_attributes))
        tid  = int(_get_first_from_list(rec, self.tid_attributes))

        trec = dict(pid=pid,tid=tid)

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
                if key.startswith("event.begin#"):
                    if "Kokkos::" in rec[key] or ("MPI_" in rec[key] and rec[key] not in all_collectives) or ("kernel_type" in keys and "kokkos.fence" in rec["kernel_type"]):
                        continue
                    self._process_event_begin_rec(rec, (pid, tid), key)
                    return
                if key.startswith("event.end#"):
                    if "Kokkos::" in rec[key] or ("MPI_" in rec[key] and rec[key] not in all_collectives) or ("kernel_type" in keys and "kokkos.fence" in rec["kernel_type"]):
                        continue
                    self._process_event_end_rec(rec, (pid, tid), key, trec)
                    break
            else:
                self.skipped += 1

        if "name" in trec:
            self.records.append(trec)

    def _process_gputrace_begin(self, rec, pid):
        block = rec.get("gputrace.block")
        skey  = ((pid,int(block)), "gputrace")
        tst   = float(rec["gputrace.timestamp"])*1e-3

        if skey in self.rstack:
            self.rstack[skey].append(tst)
        else:
            self.rstack[skey] = [ tst ]

    def _process_gputrace_end(self, rec, pid, trec):
        block = rec.get("gputrace.block")
        skey  = ((pid,int(block)), "gputrace")
        btst  = self.rstack[skey].pop()
        tst   = float(rec["gputrace.timestamp"])*1e-3

        name  = rec.get("gputrace.region")
        if isinstance(name, list):
            name = name[-1]

        trec.update(ph="X", name=name, cat="gpu", ts=btst, dur=(tst-btst), tid="block."+str(block))

    def _process_timesync_rec(self, rec, pid):
        self.tsync[pid] = _get_timestamp(rec)

    def _process_event_begin_rec(self, rec, loc, key):
        attr = key[len("event.begin#"):]
        tst  = _get_timestamp(rec)

        raw_path = rec.get("path", "")
        raw_kernel_type = rec.get("kernel_type", "")
        path = "/".join(raw_path) if isinstance(raw_path, list) and len(raw_path) > 1 else raw_path
        kernel_type = "/".join(raw_kernel_type) if isinstance(raw_kernel_type, list) and len(raw_kernel_type) > 1 else raw_kernel_type

        rank = int(rec.get("mpi.rank"))

        skey = (loc,attr)

        if skey in self.rstack:
            self.rstack[skey].append((tst, path, kernel_type, rank))
        else:
            self.rstack[skey] = [ (tst, path, kernel_type, rank) ]

    def _process_event_end_rec(self, rec, loc, key, trec):
        attr = key[len("event.end#"):]
        btst, path, kernel_type, rank = self.rstack[(loc,attr)].pop()
        tst  = _get_timestamp(rec)
        name = rec[key]

        self._get_stackframe(rec, trec)

        if "MPI_" in name:
            if name in all_collectives:
                type = "collective"
            else:
                type = "mpi"
        elif "Kokkos::" in name:
            type = "kokkos"
        else:
            type = "other"

        if name not in unique_functions:
            counters[type]["unique_count"] += 1
            unique_functions.append(name)

            tmp_name = f"{name} {path}"
            if tmp_name not in global_hierarchy_functions:
                global_hierarchy_functions.append(rec)

        counters[type]["time"] += (tst-btst)
        counters[type]["total_count"] += 1

        trec.update(ph="X", name=name, type=type, cat=attr, ts=btst, dur=(tst-btst), path=path, kernel_type=kernel_type, rank=rank)

    def _process_cupti_activity_rec(self, rec, trec):
        cat  = rec["cupti.activity.kind"]
        tst  = float(rec["cupti.activity.start"])*1e-3
        dur  = float(rec["cupti.activity.duration"])*1e-3
        name = rec.get("cupti.kernel.name", cat)

        trec.update(ph="X", name=name, cat=cat, ts=tst, dur=dur, tid="cuda")

    def _process_roctracer_activity_rec(self, rec, trec):
        cat  = rec["rocm.activity"]
        tst  = float(rec["rocm.starttime"])*1e-3
        dur  = float(rec["rocm.activity.duration"])*1e-3
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
        hwm  = float(rec["umpire.alloc.highwatermark"])
        tst  = _get_timestamp(rec)
        args = { "size": size }

        trec.update(ph="C", name=name, ts=tst, args=args)

    def _get_stackframe(self, rec, trec):
        key = "source.function#callpath.address"
        if key in rec:
            sf = self.stackframes.get_stackframe_id(rec[key], "callstack")
            trec.update(sf=sf)


def convert_cali_to_json(input_files: list, event_output_file, metadata_output_file, hierarchy_ftns_output_file):

    cfg = {
        "event_output": open(event_output_file, "w"),
        "metadata_output": open(metadata_output_file, "w"),
        "hierarchy_ftns_output": open(hierarchy_ftns_output_file, "w"),
        "pretty_print": True,
        "sync_timestamps": True,
        "counters": {},
        "tid_attributes": [],
        "pid_attributes": [],
        "verbose": False
    }

    converter = CaliTraceEventConverter(cfg)

    begin = time.perf_counter()

    for file in input_files:
        with open(file) as input:
            converter.read_and_sort(input)

    if cfg["sync_timestamps"]:
        ts = converter.start_timing("Syncing ...")
        converter.sync_timestamps()
        converter.end_timing(ts)

    ts = converter.start_timing("Writing ...")
    converter.write(cfg["event_output"], cfg["metadata_output"], cfg["hierarchy_ftns_output"])
    converter.end_timing(ts)

    cfg["event_output"].close()
    cfg["metadata_output"].close()

    end = time.perf_counter()
    tot = end - begin
    wrt = converter.written

    print(f"Done. {wrt} records written. Total {tot:.2f}s.", file=sys.stderr)
