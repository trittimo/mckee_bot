import requests
import json
import time
import msgpack
import re
import math
import sys

def log_print(o):
    print(o)
    sys.stdout.flush()

endpoint = "https://discordapp.com/api/v6"
guild = "219157162000252931"

with open("private.json", "r") as private:
    headers = json.loads(private.read())

def try_get(url, headers, params = None):
    response = requests.get(url = url, params = params, headers = headers)
    if response.status_code == requests.codes.too_many:
        result = response.json()
        sleep_time = int(math.ceil(float(result["retry_after"]) / 1000))

        log_print("Received 'too many' status code. Sleeping for " + str(sleep_time) + " seconds")
        sleep(sleep_time)
        return try_get(url, params, headers)
    elif response.status_code != requests.codes.ok:
        log_print("Received a bad response code: " + str(response.status_code))
        log_print("Url: " + url)
        log_print("Headers: " + str(headers))
        log_print("Params: " + str(params))
        log_print(response.json())
        exit(1)

    return response.json()

def get_channels(guild):
    return try_get(url = "%s/guilds/%s/channels" % (endpoint, guild), headers = headers)

def get_reactions(channel, message, emoji):
    return try_get(url = "%s/channels/%s/messages/%s/reactions/%s" % (endpoint, channel, message, emoji), headers = headers)

def get_messages(channel, before):
    params = {"limit": "100"}
    if before:
        params["before"] = before

    response = try_get(url = "%s/channels/%s/messages" % (endpoint, channel_id), headers = headers, params = params)

    for message in response:
        if not "reactions" in message:
            continue

        for reaction in message["reactions"]:
            if reaction["emoji"]["id"]:
                reaction["users"] = get_reactions(channel, message["id"], reaction["emoji"]["name"] + "%3A" + reaction["emoji"]["id"])
            else:
                reaction["users"] = get_reactions(channel, message["id"], reaction["emoji"]["name"])

    return response

for channel in filter(lambda c: c["type"] == 0, get_channels(guild)):
    channel_id = channel["id"]
    channel_name = re.sub('[^A-Za-z9-9]','',channel["name"])

    log_print("Downloading channel: " + channel_name)

    messages = []
    bucket_count = 0
    before = None

    while True:
        print("\tDownloading bucket " + str(bucket_count))
        bucket_count += 1

        result = get_messages(channel_id, before)
        messages.extend(result)

        if (len(result) == 0):
            break

        lastMsg = result[len(result) - 1]
        before = lastMsg["id"]

        log_print("\tRetrieving before date: " + lastMsg["timestamp"])

    log_print("Finished downloading channel. Total size: " + str(len(messages)) + " messages")
    log_print("Saving result to messages/" + channel_name + ".pack")
    with open("messages/" + channel_name + ".pack", "wb") as file:
        file.write(msgpack.packb(messages, use_bin_type=True))