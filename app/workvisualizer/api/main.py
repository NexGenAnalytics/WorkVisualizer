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

files_dir = os.path.join(os.getcwd(), "files")

@app.post("/api/upload")
async def upload_json_trace(file: UploadFile):
    try:
        if file.content_type != 'application/json':
            error = Exception('File Type is not JSON.')
            raise error
        contents = file.file.read()
        subprocess.run(['mkdir', '-p', 'files'])
        with open('files/raw_data.json', 'wb') as f:
            f.write(contents)
    except Exception as e:
        return {"message": f"There was an error uploading the file: {e}"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}."}


@app.get("/api/hierarchy")
def get_hierarchy_data():
    filename = "hierarchy.json"
    filepath = os.path.join(files_dir, filename)

    if os.path.isfile(filepath):
        with open(filepath) as f:
            return json.load(f)

    else:
        subprocess.run(["python", "../../../scripts/generate_full_hierarchy_data.py",
                        "-i", os.path.join(files_dir, "raw_data.json"),
                        "-od", os.path.join(files_dir),
                        "-of", filename])
        return get_hierarchy_data()

@app.get("/api/global_hierarchy")
def get_global_hierarchy_data():
    filename = "global_hierarchy.json"
    filepath = os.path.join(files_dir, filename)

    if os.path.isfile(filepath):
        with open(filepath) as f:
            return json.load(f)

    else:
        if not os.path.isfile(os.path.join(files_dir, "hierarchy.json")):
            get_hierarchy_data()

        subprocess.run(["python", "../../../scripts/generate_global_hierarchy_data.py",
                        "-i", os.path.join(files_dir, "hierarchy.json"),
                        "-od", os.path.join(files_dir),
                        "-of", filename])
        return get_global_hierarchy_data()

@app.get("/api/spacetime")
def get_spacetime_data():
    filename = "spacetime.json"
    filepath = os.path.join(files_dir, filename)

    if os.path.isfile(filepath):
        with open(filepath) as f:
            return json.load(f)

    else:
        if not os.path.isfile(os.path.join(files_dir, "hierarchy.json")):
            get_hierarchy_data()

        subprocess.run(["python", "../../../scripts/generate_spacetime_data.py",
                        "-i", os.path.join(files_dir, "hierarchy.json"),
                        "-od", os.path.join(files_dir),
                        "-of", filename])
        return get_spacetime_data()
