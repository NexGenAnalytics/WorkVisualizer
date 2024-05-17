import json
import os
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Used by SpaceTime
@app.get("/api/spacetime")
def get_spacetime_data():
    print("Getting Data")
    filename = "../../../data/d3_scatter/md_0r_100s_pruned_scatter.json"
    try:
        with open(filename) as f:
            spacetime_data = json.load(f)
        print(" Found data")
        return spacetime_data
    except FileNotFoundError:
        print(" Didn't find data")
        return {"message": "No file was uploaded."}


@app.post("/api/upload")
async def upload_json_trace(file: UploadFile):
    try:
        if file.content_type != 'application/json':
            error = Exception('File Type is not JSON.')
            raise error
        contents = file.file.read()
        subprocess.run(['mkdir', '-p', 'files'])
        with open('files/current.json', 'wb') as f:
            f.write(contents)
    except Exception as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}."}


# Used by the GlobalSunBurst and GlobalIndentedTree
@app.get("/api/global_hierarchy")
def get_global_hierarchy_data():
    filename = "../../../data/d3_hierarchy/md_0r_100s_global_hierarchy.json"
    with open(filename) as f:
        global_hierarchy_data = json.load(f)
    return global_hierarchy_data
