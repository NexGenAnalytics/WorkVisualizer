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
from hierarchy2global import hierarchy_to_global_hierarchy

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
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

def unpack_cali():
    input_files = [os.path.join(files_dir, file) for file in os.listdir(files_dir) if file.endswith(".cali")]
    if len(input_files) == 0:
        return {"message": "No input .cali file was found."}
    convert_cali_to_json(input_files, os.path.join(files_dir, "events.json"), os.path.join(files_dir, "metadata.json"), os.path.join(files_dir, "hierarchy_ftns.json"))

@app.post("/api/upload")
async def upload_json_trace(file: UploadFile):
    try:
        contents = file.file.read()
        os.makedirs(files_dir, exist_ok=True)
        remove_existing_files(files_dir)
        with open(f'{files_dir}/input_data.cali', 'wb') as f:
            f.write(contents)
    except Exception as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()

    # Then get the initial data
    unpack_cali()

    return {"message": f"Successfully uploaded {file.filename}."}

@app.get("/api/spacetime")
def get_spacetime_data():
    filename = "events.json"
    filepath = os.path.join(files_dir, filename)

    if not os.path.isfile(filepath):
        unpack_cali()

    return get_data_from_json(filepath)

@app.get("/api/hierarchy")
def get_hierarchy_data():
    filename = "hierarchy.json"
    filepath = os.path.join(files_dir, filename)

    events_file = os.path.join(files_dir, "events.json")

    if not os.path.isfile(filepath):
        if not os.path.isfile(events_file):
            unpack_cali()
        events_to_hierarchy(events_file, os.path.join(files_dir, "hierarchy.json"))

    return get_data_from_json(filepath)

@app.get("/api/global_hierarchy")
def get_global_hierarchy_data():
    filename = "global_hierarchy.json"
    filepath = os.path.join(files_dir, filename)

    events_file = os.path.join(files_dir, "events.json")
    hierarchy_file = os.path.join(files_dir, "hierarchy.json")

    if not os.path.isfile(filepath):
        if not os.path.isfile(hierarchy_file):
            if not os.path.isfile(events_file):
                unpack_cali()
            events_to_hierarchy(events_file, hierarchy_file)
        hierarchy_to_global_hierarchy(hierarchy_file, os.path.join(files_dir, "global_hierarchy.json"))

    return get_data_from_json(filepath)

@app.get("/api/util/vizcomponents")
def get_available_viz_componenents():
    directory_path = os.path.join(os.getcwd(), '..', 'app', 'ui', 'components', 'viz')

    try:
        files = os.listdir(directory_path)
        tsx_files = [file for file in files if file.endswith('.tsx')]
        print(tsx_files)
        return JSONResponse(content={"components": tsx_files})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
