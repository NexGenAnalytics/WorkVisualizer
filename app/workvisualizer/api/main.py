# app/index.py
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel

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
    filename = "../../../data/d3_scatter/md_0r_100s_pruned_scatter.json"
    with open(filename) as f:
        spacetime_data = json.load(f)
    return spacetime_data


# Used by the GlobalSunBurst and GlobalIndentedTree
@app.get("/api/global_hierarchy")
def get_global_hierarchy_data():
    filename = "../../../data/d3_hierarchy/md_0r_100s_global_hierarchy.json"
    with open(filename) as f:
        global_hierarchy_data = json.load(f)
    return global_hierarchy_data
