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
from logging_utils.logging_utils import log_timed, set_log_level
from cali2events import convert_cali_to_json
from sliceAnalysis import run_slice_analysis
from events2hierarchy import events_to_hierarchy
from aggregateMetadata import aggregate_metadata
from logical_hierarchy import generate_logical_hierarchy_from_root
import representativeRank
import timeSlice

import json
import mmap
import os
import sys
import re
from typing import List
import concurrent.futures

import numpy as np
import orjson
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

files_dir = os.path.join(os.getcwd(), "files")


@log_timed()
def remove_existing_files(directory):
    if os.path.isdir(directory):
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                remove_existing_files(full_path)


@log_timed()
def create_files_directory(files_directory):
    """Creates all directories that are used by WV."""
    os.makedirs(files_directory, exist_ok=True)

    cali_dir = os.path.join(files_directory, "cali")
    os.makedirs(cali_dir, exist_ok=True)

    events_dir = os.path.join(files_directory, "events")
    os.makedirs(events_dir, exist_ok=True)

    unique_dir = os.path.join(files_directory, "unique-events")
    os.makedirs(unique_dir, exist_ok=True)

    metadata_dir = os.path.join(files_directory, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)

    metadata_proc_dir = os.path.join(metadata_dir, "procs")
    os.makedirs(metadata_proc_dir, exist_ok=True)


# Endpoint to change the log level dynamically
@app.get("/set-log-level/{log_level}")
def set_log_level_endpoint(log_level: str):
    try:
        message = set_log_level(log_level)
        return {"message": message}
    except ValueError as e:
        return {"error": str(e)}


# Simple helper function
@log_timed()
def get_data_from_json(filepath):
    assert os.path.isfile(filepath), f"No file found at {filepath}"
    try:
        with open(filepath, 'r') as f:
            return orjson.loads(f.read())
            # for really large files:
            # with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            #     return orjson.loads(mm.read(mm.size()))
    except FileNotFoundError as e:
        sys.exit(f"Could not find {filepath}")


def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def process_chunk(chunk, files_dir, maximum_depth_limit):
    convert_cali_to_json(chunk, files_dir, maximum_depth_limit)


@log_timed()
def unpack_cali(maximum_depth_limit=None):
    cali_dir = os.path.join(files_dir, "cali")
    input_files = [os.path.join(cali_dir, filename) for filename in os.listdir(cali_dir) if filename.endswith(".cali")]

    if len(input_files) == 0:
        return {"message": "No input .cali file was found."}

    # Determine the number of CPU cores
    num_cores = os.cpu_count()
    chunk_size = max(1, len(input_files) // num_cores)  # Adjust chunk size based on the number of CPU cores

    chunks = list(chunk_list(input_files, chunk_size))

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_chunk, chunk, files_dir, maximum_depth_limit) for chunk in chunks]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    aggregate_metadata(files_dir)
    remove_existing_files(os.path.join(files_dir, "metadata", "procs"))


@app.post("/api/upload")
async def upload_cali_files(files: List[UploadFile] = File(...)):
    remove_existing_files(files_dir)
    create_files_directory(files_dir)
    cali_dir = os.path.join(files_dir, "cali")

    for file in files:
        try:
            contents = await file.read()
            with open(f"{cali_dir}/{file.filename}", "wb") as f:
                f.write(contents)
        except Exception as e:
            return {"message": f"There was an error uploading {file.filename}: {e}"}
        finally:
            await file.close()

    unpack_cali(maximum_depth_limit=5)

    return {"message": "Successfully uploaded files."}


# This endpoint doesn't use the rank at all for now
@app.get("/api/metadata/{depth}/{rank}")
@log_timed()
def get_metadata(depth):
    metadata_dir = os.path.join(files_dir, "metadata")

    depth_desc = "depth_full" if depth == "-1" else f"depth_{depth}"
    filename = f"metadata-{depth_desc}.json"
    filepath = os.path.join(metadata_dir, filename)

    if not os.path.isfile(filepath):
        unpack_cali(maximum_depth_limit=depth)

    return get_data_from_json(filepath)


@app.get("/api/eventsplot/{depth}/{rank}")
@log_timed()
def get_eventsplot_data(depth, rank):
    events_dir = os.path.join(files_dir, "events")
    depth_desc = "depth_full" if depth == "-1" else f"depth_{depth}"

    if rank == "all":
        all_rank_data = []
        at_least_one_file = False
        for file in os.listdir(events_dir):
            if file.endswith(f"{depth_desc}.json"):
                at_least_one_file = True
                all_rank_data.extend(get_data_from_json(os.path.join(events_dir, file)))

        if not at_least_one_file:
            unpack_cali(maximum_depth_limit=depth)
            at_least_one_file = True

        return all_rank_data

    filename = f"events-{rank}-{depth_desc}.json"
    filepath = os.path.join(events_dir, filename)

    if not os.path.isfile(filepath):
        unpack_cali(maximum_depth_limit=depth)

    # TODO: Add check for rank

    return get_data_from_json(filepath)


# @app.get("/api/hierarchy/{rank}")
# def get_hierarchy_data(rank):
#     filename = f"hierarchy-{rank}.json"
#     filepath = os.path.join(files_dir, filename)

#     events_file = os.path.join(files_dir, f"events-{rank}.json")

#     if not os.path.isfile(filepath):
#         if not os.path.isfile(events_file):
#             unpack_cali()
#         events_to_hierarchy(events_file, filepath)

#     return get_data_from_json(filepath)

@app.get("/api/logical_hierarchy/{ftn_id}/{depth}/{rank}")
@log_timed()
def get_logical_hierarchy_data(ftn_id, depth, rank):
    unique_dir = os.path.join(files_dir, "unique-events")

    logical_dir = os.path.join(files_dir, "logical_hierarchy")

    root_desc = "root" if ftn_id == "-1" else f"root_{ftn_id}"
    depth_desc = "depth_full" if depth == "-1" else f"depth_{depth}"
    filename = f"logical_hierarchy_rank_{rank}_root_{root_desc}_{depth_desc}.json"
    filepath = os.path.join(logical_dir, filename)

    unique_events_file = os.path.join(unique_dir, f"unique-events-{rank}-{depth_desc}.json")
    if not os.path.isfile(filepath):
        if not os.path.isfile(unique_events_file):
            unpack_cali(maximum_depth_limit=depth)

        # TODO: Add check for rank
        generate_logical_hierarchy_from_root(unique_events_file, filepath, ftn_id=int(ftn_id))

    return get_data_from_json(filepath)


@app.get("/api/util/vizcomponents")
@log_timed()
def get_available_viz_componenents():
    viz_components_dir = os.path.join(os.getcwd(), '..', 'app', 'ui', 'components', 'viz')

    try:
        files = os.listdir(viz_components_dir)
        tsx_files = [file for file in files if file.endswith('.tsx')]
        print(tsx_files)
        return JSONResponse(content={"components": tsx_files})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/representativerank")
@log_timed()
def get_representative_rank():
    try:
        # this is quite barebones; this will need to handle depth selection,
        # and function type selection (ie cluster based on kokkos, mpi, user, etc. functions)
        analysis_dir = os.path.join(files_dir, "analysis")

        filename = f"representative_rank.json"
        filepath = os.path.join(analysis_dir, filename)

        if not os.path.isfile(filepath):
            analyze_representative_rank()

        return get_data_from_json(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/rankclusters")
@log_timed()
def get_rank_clusters():
    try:
        # this is quite barebones; this will need to handle depth selection,
        # and function type selection (ie cluster based on kokkos, mpi, user, etc. functions)
        analysis_dir = os.path.join(files_dir, "analysis")

        filename = f"rank_clusters.json"
        filepath = os.path.join(analysis_dir, filename)

        if not os.path.isfile(filepath):
            analyze_representative_rank()

        return get_data_from_json(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@log_timed()
def analyze_representative_rank():
    events_dir = os.path.join(files_dir, "events")
    files = os.listdir(events_dir)
    abs_files = [os.path.abspath(os.path.join(events_dir, file)) for file in files]
    print(f"files: {files}")
    unique_function_names = representativeRank.get_unique_function_names(abs_files)
    print(unique_function_names)

    def extract_rank(s):
        match = re.search(r'events-(\d+)-depth', s)
        if match:
            return int(match.group(1))
        return None

    ranks = [extract_rank(filename) for filename in files]
    print(f"ranks: {ranks}")
    file_name_template = str(
        os.path.abspath(os.path.join(events_dir, "events-{}-depth_5.json")))  # @todo fix this hardcoded depth
    feature_df = representativeRank.create_feature_dataframe(
        file_name_template=file_name_template,
        ranks=ranks,
        function_names=unique_function_names
    )
    print(feature_df)
    scaled_df = representativeRank.scale_dataframe(feature_df)
    print(scaled_df)
    data_scaled_pca_df, loadings_df = representativeRank.apply_pca(scaled_df)
    print(data_scaled_pca_df)
    print(loadings_df)
    kmeans, n_clusters, df = representativeRank.apply_kmeans(data_scaled_pca_df, len(ranks))
    if kmeans is None and n_clusters == 1:
        json_response = {'representative rank': ranks[0]}
    else:
        print(kmeans)
        print(f"There are {n_clusters} clusters")
        print(df)
        # get number of points per cluster
        representative_ranks = representativeRank.get_representative_ranks_of_clusters(df, kmeans, ranks)
        print(representative_ranks)
        for cluster in np.unique(kmeans.labels_):
            print(f"Cluster {cluster} has {len(df[df['cluster'] == cluster])} points")
        res = [
            {
                "cluster": cluster,
                "representative rank": representative_ranks[f"cluster {cluster}"],
                "n_ranks": len(df[df['cluster'] == cluster])
            } for cluster in np.unique(kmeans.labels_)
        ]

        print(res)
        max_ranks_per_cluster = 0
        representative_rank = 0
        for cluster in res:
            if cluster['n_ranks'] > max_ranks_per_cluster:
                max_ranks_per_cluster = cluster['n_ranks']
                representative_rank = cluster['representative rank']

        json_response = {'representative rank': representative_rank.split("rank ")[1]}

    # Create json for clusters
    # cluster_json = {cluster_id: {"ranks": []} for cluster_id in range(n_clusters)}
    print()
    analysis_dir = os.path.join(files_dir, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    cluster_json = df.groupby('cluster').apply(lambda x: x.index.tolist()).to_dict()
    filename = f"rank_clusters.json"
    clusters_filepath = os.path.join(analysis_dir, filename)
    with open(clusters_filepath, 'w', encoding='utf-8') as f:
        json.dump(cluster_json, f, ensure_ascii=False, indent=4)
    print()

    filename = f"representative_rank.json"
    filepath = os.path.join(analysis_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_response, f, ensure_ascii=False, indent=4)


@app.get("/api/analysis/timeslices")
@log_timed()
def get_timeslices():
    try:
        analysis_dir = os.path.join(files_dir, "analysis")

        filename = f"timeslices.json"
        filepath = os.path.join(analysis_dir, filename)

        if not os.path.isfile(filepath):
            analyze_timeslices()

        return get_data_from_json(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@log_timed()
def analyze_timeslices():
    events_dir = os.path.join(files_dir, "events")
    file_name_template = str(
        os.path.abspath(os.path.join(events_dir, "events-{}-depth_5.json")))

    representative_rank = get_representative_rank()

    # extract rank number out of representative_rank string that is of form "rank 0"
    representative_rank = representative_rank['representative rank']

    allreduce_df = timeSlice.prepare_data_for_rank(file_name_template, representative_rank)
    clustered_df = timeSlice.cluster_collectives(allreduce_df)
    metadata_dir = os.path.join(files_dir, "metadata")
    # file is whatever file in metadata_dir that starts with metadata
    filename = [file for file in os.listdir(metadata_dir) if file.startswith("metadata")][0]
    filepath = os.path.join(metadata_dir, filename)
    metadata = get_data_from_json(filepath)
    program_runtime = metadata['program.runtime']
    num_ranks = int(metadata['mpi.world.size'])
    slices = timeSlice.define_slices(clustered_df, total_runtime=program_runtime)

    rank_slice_time_lost, slice_time_lost = run_slice_analysis(files_dir, representative_rank, slices)

    # Simplify rank slice time lost for now
    simplified_rank_slice_time_lost = {}
    for ranks_list in rank_slice_time_lost.values():
        for ranks_dict in ranks_list:
            simplified_rank_slice_time_lost[ranks_dict["slice"]] = {
                f"Rank {ranks_dict['rank']}": f"Lost the most time ({abs(ranks_dict['time_lost']):2f} seconds slower than the representative rank)" for ranks_dict in ranks_list
            }

    for slice_id in range(len(slices)):
        if slice_id not in list(simplified_rank_slice_time_lost.keys()):
            simplified_rank_slice_time_lost[slice_id] = {"": "No significant time-losing ranks in this slice."}

    # modify the slices so they have 'slice ...' as the key and the times are stores in the 'ts' sub-key
    slices = {
        i: {
            "ts": [ts for ts in slice_data],
            "time_lost": f'{slice_time_lost[i]/num_ranks:2f}',
            "statistics": simplified_rank_slice_time_lost[i]
        } for i, slice_data in enumerate(slices)
    }

    analysis_dir = os.path.join(files_dir, "analysis")
    # create the analysis directory if it does not exist
    # os.makedirs(analysis_dir, exist_ok=True)
    filename = f"timeslices.json"
    filepath = os.path.join(analysis_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(slices, f, ensure_ascii=False, indent=4)