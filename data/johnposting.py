# Combines the separate .pack files into one .json file
import json
import os
import requests
import hashlib

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

with open("json_messages/johnposting.json") as f:
    messages = json.load(f)


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


with open("private.json") as f:
    headers = json.load(f)

count = 0
for attachment in urls:
    if count % 10 == 0:
        print(f"{count} / {len(urls)}")
    dl = try_get(attachment["url"], None)
    _, ext = os.path.splitext(attachment["filename"])
    name = "johnposting/" + str(hashlib.md5(dl).hexdigest()) + ext
    with open(name, "wb") as f:
        f.write(dl)
    count += 1