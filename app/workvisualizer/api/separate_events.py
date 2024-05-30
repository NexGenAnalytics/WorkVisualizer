import os
import json

def separate_events(input_file, output_stem):
    with open(input_file) as f:
        json_data = json.load(f)

    separate_lists = {}

    for event in json_data:
        type = event["type"]
        if type not in separate_lists:
            separate_lists[type] = []
        separate_lists[type].append(event)

    for type, list in separate_lists:
        output_file = os.path.join(output_stem, f"{type}_events.json")
        with open(output_file, "w") as out_json:
            json.dump(list, out_json, indent=4)
