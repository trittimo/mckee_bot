import msgpack
import sys
import json
import csv
import os
from datetime import datetime

with open("server.json") as f:
    server = json.loads(f.read())

channels = {c["id"]: c["name"] for c in server["channels"]}

lines = [["Message ID", "Username", "Channel", "Message", "Timestamp", "Edited", "Upvotes", "Downvotes"]]
attachments = [["Message ID", "Filename", "Url", "Size"]]
reactions = [["Message ID", "Emoji", "User Reacting"]]

(_,_,file_names) = next(os.walk("messages"))
for file_name in file_names:
    if not file_name.endswith(".pack"):
        continue
    with open("messages/" + file_name, "rb") as result_file:
        data = msgpack.unpackb(result_file.read(), raw=False)
    for comment in data:
        mid = comment["id"]
        username = comment["author"]["username"]
        channel = channels[comment["channel_id"]]
        message = comment["content"]
        edited = comment["edited_timestamp"] or ""

        if edited:
            edited = datetime.fromisoformat(edited).strftime("%Y-%m-%d %I:%M:%S %p")

        time = datetime.fromisoformat(comment["timestamp"]).strftime("%Y-%m-%d %I:%M:%S %p")

        upvotes = 0
        downvotes = 0
        if "reactions" in comment:
            for reaction in comment["reactions"]:
                if reaction["emoji"]["name"] == "reddit_upvote":
                    upvotes += reaction["count"]
                elif reaction["emoji"]["name"] == "reddit_downvote":
                    downvotes += reaction["count"]

        lines.append([mid, username, channel, message, time, edited, upvotes, downvotes])

        if "attachments" in comment:
            for attach in comment["attachments"]:
                filename = attach["filename"]
                url = attach["url"]
                size = attach["size"]
                attachments.append([mid, filename, url, size])
        
        if "reactions" in comment:
            for react in comment["reactions"]:
                emoji = react["emoji"]["name"]
                for user in react["users"]:
                    name = user["username"]
                    reactions.append([mid, emoji, name])

if not os.path.exists("messages_csv"):
    os.mkdir("messages_csv")

with open("messages_csv/messages.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(lines)

with open("messages_csv/reactions.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(reactions)

with open("messages_csv/attachments.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(attachments)