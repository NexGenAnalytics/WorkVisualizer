import json
import os
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel
import subprocess

from cali2events import convert_cali_to_json
from events2hierarchy import events_to_hierarchy
from logical_hierarchy import generate_logical_hierarchy_from_root

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

files_dir = os.path.join(os.getcwd(), "files")

# Simple helper function
def get_data_from_json(filepath):
    assert os.path.isfile(filepath), f"No file found at {filepath}"
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError as e:
        sys.exit(f"Could not find {filepath}")

def remove_existing_files(directory):
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            remove_existing_files(full_path)

def unpack_cali(maximum_depth_limit=None):
    cali_dir = os.path.join(files_dir, "cali")
    input_files = [os.path.join(cali_dir, filename) for filename in os.listdir(cali_dir) if filename.endswith(".cali")]

    if len(input_files) == 0:
        return {"message": "No input .cali file was found."}

    convert_cali_to_json(input_files, files_dir, maximum_depth_limit)

@app.post("/api/upload")
async def upload_cali_files(files: list[UploadFile] = File(...)):
    os.makedirs(files_dir, exist_ok=True)
    remove_existing_files(files_dir)

    cali_dir = os.path.join(files_dir, "cali")
    os.makedirs(cali_dir, exist_ok=True)

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
def get_metadata(depth, rank):
    metadata_dir = os.path.join(files_dir, "metadata")

    depth_desc = "depth_full" if depth == "-1" else f"depth_{depth}"
    filename = f"metadata-{depth_desc}.json"
    filepath = os.path.join(metadata_dir, filename)

    if not os.path.isfile(filepath):
        unpack_cali(maximum_depth_limit=depth)

    return get_data_from_json(filepath)

@app.get("/api/spacetime/{depth}/{rank}")
def get_spacetime_data(depth, rank):
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
def get_logical_hierarchy_data(ftn_id, depth, rank):
    unique_dir = os.path.join(files_dir, "unique-events")

    logical_dir = os.path.join(files_dir, "logical_hierarchy")

    root_desc = "root" if ftn_id == "-1" else f"root_{ftn_id}"
    depth_desc = "depth_full" if depth == "-1" else f"depth_{depth}"
    filename = f"logical_hierarchy_rank_{rank}_root_{root_desc}_{depth_desc}.json"
    filepath = os.path.join(logical_dir, filename)

    unique_events_file = os.path.join(unique_dir, f"unique-events-{rank}-{depth_desc}.json")
    print(unique_events_file)
    if not os.path.isfile(filepath):
        if not os.path.isfile(unique_events_file):
            unpack_cali(maximum_depth_limit=depth)

        # TODO: Add check for rank
        generate_logical_hierarchy_from_root(unique_events_file, filepath, ftn_id=int(ftn_id))

    return get_data_from_json(filepath)

@app.get("/api/util/vizcomponents")
def get_available_viz_componenents():
    viz_components_dir = os.path.join(os.getcwd(), '..', 'app', 'ui', 'components', 'viz')

    try:
        files = os.listdir(viz_components_dir)
        tsx_files = [file for file in files if file.endswith('.tsx')]
        print(tsx_files)
        return JSONResponse(content={"components": tsx_files})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
