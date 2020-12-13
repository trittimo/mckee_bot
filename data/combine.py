# Combines the separate .pack files into one .json file
import json
import msgpack
import os

if not os.path.exists("messages"):
    print("You haven't downloaded any messages yet... use download.py first")
    exit(1)

if not os.path.exists("json_messages"):
    os.mkdir("json_messages")

(path, dirs, files) = next(os.walk("messages"))

result = {}

with open("server.json") as f:
    server = json.loads(f.read())

result["server"] = server
channels = {c["id"]: c["name"] for c in server["channels"]}

for f in files:
    if not f.endswith(".pack"):
        continue
    with open(os.path.join(path, f), "rb") as pack_file:
        data = msgpack.unpackb(pack_file.read(), raw=False)

    if not data:
        continue
    
    channel_id = data[0]["channel_id"]
    channel_name = channels[channel_id]
    result[channel_name] = data

with open("json_messages/all.json", "w") as f:
    json.dump(result, f)