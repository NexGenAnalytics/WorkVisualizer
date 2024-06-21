import os
import json

mock_hierarchy_file = os.path.join(os.getcwd(), "mock_hierarchy.json")
with open(mock_hierarchy_file) as f:
    mock_hierarchy = json.load(f)

