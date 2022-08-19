import requests
import json
import time
import msgpack
import re
import math
import sys
import os

def log_print(o):
    print(o)
    sys.stdout.flush()

endpoint = "https://discord.com/api/v9"

if not os.path.exists("private.json"):
    print("The working directory must include a private.json file")
    print("The json file should contain the headers that will be sent to the Discord API")
    print("You can get this by looking in the developer tools in Discord")
    exit(1)

if not os.path.exists("settings.json"):
    print("The working directory must include a settings.json file")
    print("You must at the very least include the guild id (i.e. server) you are trying to access")
    exit(1)

with open("private.json", "r") as private:
    headers = json.loads(private.read())

with open("settings.json", "r") as f:
    settings = json.loads(f.read())

if not "guild" in settings:
    print("The settings.json file must include a valid guild ID")
    exit(1)

def try_get(url, headers, params = None):
    attempts = 0
    while attempts < 20:
        try:
            response = requests.get(url = url, params = params, headers = headers)
        except: # Probably a timeout. Just try again
            log_print("Encountered exception while calling requests.get")
            attempts += 1
            continue
        if response.status_code == requests.codes.too_many:
            result = response.json()
            sleep_time = int(math.ceil(float(result["retry_after"]) / 1000)) * 5

            log_print("Received 'too many' status code. Sleeping for " + str(sleep_time) + " seconds")
            time.sleep(sleep_time)
            attempts += 1
            continue
        elif response.status_code == requests.codes.forbidden:
            log_print("Not allowed to access this channel. Skipping")
            return None
        elif response.status_code != requests.codes.ok:
            log_print("Received a bad response code: " + str(response.status_code))
            log_print("Url: " + url)
            log_print("Headers: " + str(headers))
            log_print("Params: " + str(params))
            log_print(response.json())
            time.sleep(5)
            attempts += 1
            continue
        return response.json()
    log_print("Exceeded maximum allowed retries. Exiting program")
    exit(1)

def get_channels(guild):
    return try_get(url = "%s/guilds/%s/channels" % (endpoint, guild), headers = headers)

def get_reactions(channel, message, emoji):
    return try_get(url = "%s/channels/%s/messages/%s/reactions/%s" % (endpoint, channel, message, emoji), headers = headers)

def get_messages(channel, before):
    params = {"limit": "100"}
    if before:
        params["before"] = before

    response = try_get(url = "%s/channels/%s/messages" % (endpoint, channel_id), headers = headers, params = params)

    if not response:
        return []

    for message in response:
        if not "reactions" in message:
            continue

        for reaction in message["reactions"]:
            if reaction["emoji"]["id"]:
                reaction["users"] = get_reactions(channel, message["id"], reaction["emoji"]["name"] + "%3A" + reaction["emoji"]["id"])
            else:
                reaction["users"] = get_reactions(channel, message["id"], reaction["emoji"]["name"])

    return response

if __name__ == "__main__":
    for channel in filter(lambda c: c["type"] == 0, get_channels(settings["guild"])): # type: ignore
        if "include" in settings and not channel["name"] in settings["include"]:
            print("Channel '" + channel["name"] + "' not in include list")
            continue
        elif "exclude" in settings and channel["name"] in settings["exclude"]:
            print("Channel '" + channel["name"] + "' in exclude list")
            continue

        channel_id = channel["id"]
        channel_name = re.sub('[^A-Za-z0-9]','',channel["name"])

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
        if len(messages) == 0:
            log_print("Not saving messages because there are no messages to save")
            continue

        log_print("Saving result to messages/" + channel_name + ".pack")

        if not os.path.isdir("messages"):
            os.mkdir("messages")

        with open("messages/" + channel_name + ".pack", "wb") as file:
            file.write(msgpack.packb(messages, use_bin_type=True)) # type: ignore