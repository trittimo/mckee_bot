from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os
import json
import msgpack
import sys
import csv
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

def analyze(messages):
    sid = SentimentIntensityAnalyzer()
    result = []
    for message in messages:
        text = message["content"]
        score = sid.polarity_scores(text)
        result.append((message, score))
    return result

def save_results(scores, filename):
    if not os.path.exists("sentiment"):
        os.mkdir("sentiment")
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Author", "Channel", "Time", "Message", "Positive", "Negative", "Neutral", "Compound"])
        for (message, score) in scores:
            time = message["time"].isoformat()
            writer.writerow([
                message["id"],
                message["author"],
                message["channel"],
                time,
                message["content"],
                score["pos"],
                score["neg"],
                score["neu"],
                score["compound"]
            ])

def print_help():
    print("Usage: python3 sentiment.py by_user [user]")
    print("Usage: python3 sentiment.py by_channel [channel]")
    print("Usage: python3 sentiment.py all")
    print("Usage: python3 sentiment.py chart [sentiment file]")
    exit(1)

def create_chart(filename):
    print("Creating chart for %s" % filename)
    messages = {}
    d0 = None
    d1 = None
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for line in reader:
            line["Time"] = datetime.fromisoformat(line["Time"])
            if not d0:
                d0 = line["Time"]
            d1 = line["Time"]
            line["Positive"] = float(line["Positive"])
            line["Negative"] = float(line["Negative"])
            line["Neutral"] = float(line["Neutral"])
            line["Compound"] = float(line["Compound"])
            if not line["Author"] in messages:
                messages[line["Author"]] = []

            messages[line["Author"]].append(line)

    titles = [user for user in messages]
    fig = make_subplots(rows=int(len(messages) / 2) + (len(messages) % 2), cols=2, subplot_titles=titles)
    fig.update_layout(showlegend=False)
    curr_index = 0
    for user in messages:
        granularity = 10
        dates = d1 - np.arange(int((d1 - d0).days / granularity)) * timedelta(days=granularity)
        total_days = d1 - d0
        dates = np.flip(dates)
        scores = np.zeros(len(dates))
        for message in messages[user]:
            # Could have used a bisect here, but eh
            box = int((message["Time"] - d0).days / 10) - 1
            scores[box] += message["Compound"]
        fig.add_trace(go.Scatter(x = dates, y = scores), row = int(curr_index / 2) + 1, col = (curr_index % 2) + 1)
        curr_index += 1

    fig.update_layout(height=(len(titles) * 200), width=1200, title_text="Positivity over time")
    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    fig.write_html("graphs/positivity_over_time.html")
    print("Saved chart to graphs/positivity_over_time.html")

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Missing required argument: analysis type")
        print_help()

    if not os.path.exists("messages"):
        print("No message data to analyze")
        exit(1)
    
    if not os.path.exists("server.json"):
        print("No server.json file (run probe.py)")
        exit(1)

    print("Loading server data")

    with open("server.json") as f:
        server = json.loads(f.read())

    print("Loading messages")

    server_channels = None
    messages = None
    if sys.argv[1] != "chart":
        server_channels = {c["id"]: c["name"] for c in server["channels"]}
        (_,_,file_names) = next(os.walk("messages"))
        messages = {}
        for file_name in file_names:
            if not file_name.endswith(".pack"):
                continue
            with open("messages/" + file_name, "rb") as f:
                data = msgpack.unpackb(f.read(), raw=False)
            if len(data) > 0:
                channel = server_channels[data[0]["channel_id"]]
                if not channel in messages:
                    messages[channel] = []
                for message in data:
                    messages[channel].append({
                        "content": message["content"],
                        "author": message["author"]["username"],
                        "id": message["id"],
                        "channel": channel,
                        "time": datetime.fromisoformat(message["timestamp"])
                })

    if sys.argv[1] == "chart":
        if len(sys.argv) <= 2:
            print("Missing required argument: [file]")
            print_help()

        if not os.path.exists(sys.argv[2]):
            print("No such file to create chart for")
            exit(1)

        create_chart(sys.argv[2])
    elif sys.argv[1] == "by_user":
        if len(sys.argv) <= 2:
            print("Missing required argument: [user]")
            print_help()

        print("Running by_user analysis on " + sys.argv[2])
        user_messages = []
        for channel in messages:
            for message in messages[channel]:
                if message["author"].lower() != sys.argv[2].lower():
                    continue
                if not message["content"]:
                    continue
                user_messages.append(message)

        if len(user_messages) == 0:
            print("Cannot analyze -- No messages from that user")
            exit(1)

        user_messages.sort(key = lambda m: m["time"])
        scores = analyze(user_messages)

        filename = "sentiment/by_user_%s.csv" % sys.argv[2].lower()
        print("Finished analysis. Dumping results to %s" % filename)
        save_results(scores, filename)
    elif sys.argv[1] == "all":
        print("Running analysis on all users")
        user_messages = []
        for channel in messages:
            for message in messages[channel]:
                if not message["content"]:
                    continue
                user_messages.append(message)

        if len(user_messages) == 0:
            print("Cannot analyze -- No messages from users")
            exit(1)

        user_messages.sort(key = lambda m: m["time"])
        scores = analyze(user_messages)

        filename = "sentiment/all_users.csv"
        print("Finished analysis. Dumping results to %s" % filename)
        save_results(scores, filename)
    else:
        print("Unsupported operation")
        exit(1)