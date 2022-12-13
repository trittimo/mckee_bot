# Combines the separate .pack files into one .json file
import json
import os
import requests
import hashlib

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

messages = []
for channel in settings["include"]:
    with open(f"json_messages/{channel}.json") as f:
        messages.extend(json.load(f))

def try_get(url, headers, params = None):
    attempts = 0
    while attempts < 20:
        try:
            response = requests.get(url = url, params = params, headers = headers)
        except: # Probably a timeout. Just try again
            print("Encountered exception while calling requests.get")
            attempts += 1
            continue
        if response.status_code == requests.codes.too_many:
            result = response.json()
            sleep_time = int(math.ceil(float(result["retry_after"]) / 1000)) * 5

            print("Received 'too many' status code. Sleeping for " + str(sleep_time) + " seconds")
            time.sleep(sleep_time)
            attempts += 1
            continue
        elif response.status_code == requests.codes.forbidden:
            print("Not allowed to access this channel. Skipping")
            return None
        elif response.status_code != requests.codes.ok:
            print("Received a bad response code: " + str(response.status_code))
            print("Url: " + url)
            print("Headers: " + str(headers))
            print("Params: " + str(params))
            print(response.json())
            time.sleep(5)
            attempts += 1
            continue
        return response.content
    print("Exceeded maximum allowed retries. Exiting program")
    exit(1)


urls = []
for message in messages:
    if not "attachments" in message:
        continue
    
    for attachment in message["attachments"]:
        if not "url" in attachment or not "filename" in attachment:
            continue

        filename = attachment["filename"]
        
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if not ext in [".jpg", ".png", ".jpeg", ".gif"]:
            continue
        urls.append(attachment)

if not os.path.exists("images"):
    os.mkdir("images")

count = 0
for attachment in urls:
    if count % 10 == 0:
        print(f"{count} / {len(urls)}")
    dl = try_get(attachment["url"], None)
    _, ext = os.path.splitext(attachment["filename"])
    name = "images/" + str(hashlib.md5(dl).hexdigest()) + ext
    with open(name, "wb") as f:
        f.write(dl)
    count += 1