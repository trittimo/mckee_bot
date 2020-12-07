import requests
import json
import time
import msgpack
import re
import math
import sys

# Saves some information about the server to a json file

def log_print(o):
    print(o)
    sys.stdout.flush()

if not len(sys.argv) > 1:
    print("You must provide a guild ID to operate on")
    exit(1)

endpoint = "https://discordapp.com/api/v6"
guild = sys.argv[1]
retry_attempts = 0

with open("private.json", "r") as private:
    headers = json.loads(private.read())

def try_get(url, headers, params = None):
    response = requests.get(url = url, params = params, headers = headers)

    attempts = 0
    while attempts < 3:
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

with open("server.json", "w") as f:
    data = {"channels": get_channels(guild)}
    f.write(json.dumps(data, sort_keys=True, indent=4))