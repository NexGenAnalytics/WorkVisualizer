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

@app.get("/api/tree")
def get_tree_data():
    print("Getting Data!")
    filename = "../../../data/pruned/md_0r_100s_pruned.json"
    with open(filename) as f:
        tree_data = json.load(f)
    return tree_data
