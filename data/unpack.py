import msgpack
import os
import json

(_,_,file_names) = next(os.walk("messages"))
for file_name in file_names:
    if not file_name.endswith(".pack"):
        print("Skipping " + file_name)
        continue
    print("Reading " + file_name)
    with open("messages/" + file_name, "rb") as result_file:
        data = msgpack.unpackb(result_file.read(), raw=False)
    
    if not os.path.exists("json_messages"):
        os.mkdir("json_messages")
    
    print("Writing " + "json_messages/" + file_name[0:-5] + ".json")
    with open("json_messages/" + file_name[0:-5] + ".json", "w") as f:
        f.write(json.dumps(data, sort_keys=True, indent=4))