import json

with open("collections.json", "r") as f:
    data = json.load(f)
    for item in data:
        if not item["year"]:
            print(item["name"])
        else:
            print(item["year"])