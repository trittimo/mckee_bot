import msgpack
import os
import csv
from collections.abc import MutableMapping, Collection

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        elif isinstance(v, Collection):
            if k == "embeds":
                built_result = ""
                for embed in v:
                    built_result += embed["url"] + "\n"
                built_result = built_result.strip()
                items.append((k, built_result))
            elif k == "reactions":
                built_result = ""
                for reaction in v["emoji"]:
                    
                    for user in reaction["users"]:

            else:
                items.append((new_key, v))
        else:
            items.append((new_key, v))
    return dict(items)

(_,_,file_names) = next(os.walk("messages"))

for file_name in file_names:

    result_headers = {}
    result = []
    if not file_name.endswith(".pack"):
        print("Skipping " + file_name)
        continue
    print("Reading " + file_name)
    with open("messages/" + file_name, "rb") as result_file:
        data = msgpack.unpackb(result_file.read(), raw=False)
    
    if not os.path.exists("csv_messages"):
        os.mkdir("csv_messages")
    
    for item in data:
        flattened = flatten(item)
        result.append(flattened)
        for header in flattened:
            result_headers[header] = True

    print("Writing " + "csv_messages/" + file_name[0:-5] + ".csv")
    with open("csv_messages/" + file_name[0:-5] + ".csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames = [k for k in result_headers])
        writer.writeheader()
        for item in result:
            writer.writerow(item)

