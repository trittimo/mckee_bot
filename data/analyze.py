import msgpack
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from tabulate import tabulate
from datetime import datetime
from datetime import date
from datetime import timedelta
import numpy as np
from bisect import bisect
import json

most_upvotes = {}
highest_upvotes = {}
comment_count = {}
given_emojis = {}
given_upvotes = {}
given_downvotes = {}
msg_timestamps = {}
total_upvotes = {}
total_downvotes = {}
embeds = {}
image_counts = {}
video_counts = {}
link_counts = {}
attachment_counts = {}

messages = {}

with open("server.json") as f:
    server = json.loads(f.read())

server_channels = {c["id"]: c["name"] for c in server["channels"]}

(_,_,file_names) = next(os.walk("messages"))
for file_name in file_names:
    if not file_name.endswith(".pack"):
        continue
    with open("messages/" + file_name, "rb") as result_file:
        data = msgpack.unpackb(result_file.read(), raw=False)
    if len(data) > 0:
        channel = server_channels[data[0]["channel_id"]]
        if not channel in messages:
            messages[channel] = data
    for comment in data:
        username = comment["author"]["username"]
        if not username in most_upvotes:
            total_upvotes[username] = 0
            total_downvotes[username] = 0
            most_upvotes[username] = 0
            highest_upvotes[username] = 0
            comment_count[username] = 0
            msg_timestamps[username] = []
            embeds[username] = 0
            image_counts[username] = 0
            video_counts[username] = 0
            link_counts[username] = 0
            attachment_counts[username] = 0

        comment_count[username] += 1
        msg_timestamps[username].append(datetime.fromisoformat(comment["timestamp"]))

        if "embeds" in comment and len(comment["embeds"]) > 0:
            for embed in comment["embeds"]:
                embeds[username] += 1
                em_type = embed["type"]
                if em_type in ["image", "gifv"]:
                    image_counts[username] += 1
                if em_type in ["article", "link", "rich", "tweet"]:
                    link_counts[username] += 1
                if em_type == "video":
                    video_counts[username] += 1

        if "attachments" in comment and len(comment["attachments"]) > 0:
            embeds[username] += 1

            for attachment in comment["attachments"]:
                attachment_counts[username] += 1


        if not "reactions" in comment:
            continue
        for reaction in comment["reactions"]:
            for giver in reaction["users"]:
                giver_username = giver["username"]
                if not giver_username in given_emojis:
                    given_emojis[giver_username] = 0
                    given_upvotes[giver_username] = 0
                    given_downvotes[giver_username] = 0

                if reaction["emoji"]["name"] == "reddit_upvote":
                    given_upvotes[giver_username] += 1
                elif reaction["emoji"]["name"] == "reddit_downvote":
                    given_downvotes[giver_username] += 1

                given_emojis[giver_username] += 1

            count = reaction["count"]
            if reaction["emoji"]["name"] == "reddit_upvote":
                total_upvotes[username] += count
            
            if reaction["emoji"]["name"] == "reddit_downvote":
                total_downvotes[username] += count

            most_upvotes[username] += count
            if count > highest_upvotes[username]:
                highest_upvotes[username] = count

def print_reaction_data():
    sort = {k: v for k, v in sorted(given_emojis.items(), key=lambda i: i[1], reverse=True)}
    headers = ["User", "Reactions given", "Upvotes given", "Downvotes given", "Other given", "Upvote/Downvote Ratio"]
    result = []
    for k in sort:
        up = 0 if not k in given_upvotes else given_upvotes[k]
        down = 0 if not k in given_downvotes else given_downvotes[k]
        if down != 0:
            ratio = "%.1f" % (float(up) / float(down))
        else:
            ratio = "N/A"

        other = sort[k] - up - down

        result.append([k, sort[k], up, down, other, ratio])

    print(tabulate(result, headers=headers,tablefmt="fancy_grid"))

def print_reaction_totals():
    sort = {k: v for k, v in sorted(total_upvotes.items(), key=lambda i: i[1], reverse=True)}
    headers = ["User", "Upvotes received"]
    result = []
    for user in sort:
        if sort[user] == 0:
            continue
        result.append([user, sort[user]])
    
    print(tabulate(result, headers=headers, tablefmt="fancy_grid"))

def show_reaction_graph(emoji_name):
    # First accumulate reaction data for all users

    accum = {}
    for channel in messages:
        for message in messages[channel]:
            poster = message["author"]["username"]
            message_date = datetime.fromisoformat(message["timestamp"])

            if not "reactions" in message:
                continue

            if not poster in accum:
                accum[poster] = []

            for reaction in message["reactions"]:
                reaction_name = reaction["emoji"]["name"]
                if reaction_name != emoji_name:
                    continue
                reaction_count = reaction["count"]
                accum[poster].append([message_date, reaction_count])

    init = datetime(2020, 12, 6)
    times = [(init + x).strftime("%I %p") for x in (np.arange(24) * timedelta(hours=1))]
    d0 = date(2016, 8, 27) # Server start


    titles = [user for user in accum]
    fig = make_subplots(rows=int(len(accum) / 2) + (len(accum) % 2), cols=2, subplot_titles=titles)
    fig.update_layout(showlegend=False)

    curr_index = 0
    for user in titles:
        sort = sorted(accum[user], key=lambda i: i[0], reverse=False)
        granularity = 10
        dates = init.date() - np.arange(int((init.date() - d0).days / granularity)) * timedelta(days=granularity)
        total_days = init.date() - d0
        dates = np.flip(dates)
        upvotes = np.zeros(len(dates))
        for item in sort:
            box = int((item[0].date() - d0).days / 10) - 1
            upvotes[box] += item[1]

        fig.add_trace(go.Scatter(x = dates, y = upvotes), row = int(curr_index / 2) + 1, col = (curr_index % 2) + 1)
        curr_index += 1

    fig.update_layout(height=1800, width=1200, title_text=emoji_name + "s over time")
    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    fig.write_html("graphs/%s_over_time.html" % emoji_name)

def show_time_graph(user):
    init = datetime(2020, 12, 6)
    times = [(init + x).strftime("%I %p") for x in (np.arange(24) * timedelta(hours=1))]
    d0 = date(2016, 8, 27) # Start of the server
    today = datetime.today().date()
    granularity = 10
    dates = today - np.arange(int((today - d0).days / granularity)) * timedelta(days=granularity)
    dates = np.flip(dates)
    values = []
    for i in range(24):
        current = np.zeros(len(dates))
        for time in msg_timestamps[user]:
            if time.hour == i:
                insert_index = bisect(dates, time.date())
                if (insert_index < len(current)):
                    current[insert_index] += 1
        values.append(current)

    fig = go.Figure(data = go.Heatmap(
        z=values,
        x=dates,
        y=times,
        colorscale='Viridis'))

    fig.update_layout(
        title=user + ' posts by hour',
        xaxis_nticks = 35)
    
    fig.show()

def show_messages_by_date():
    d0 = date(2016, 8, 27) # Start of the server
    d1 = date(2020, 12, 6) # End of the download
    granularity = 7
    dates = d1 - np.arange(int((d1 - d0).days / granularity)) * timedelta(days=granularity)
    dates = np.flip(dates)
    users = [u for u in msg_timestamps if len(msg_timestamps[u]) >= 100 and u != "Rythm" and u != "NotSoBot"]
    values = []
    for user in users:
        current = np.zeros(len(dates))
        for d in msg_timestamps[user]:
            insert_index = bisect(dates, d.date())
            
            if (insert_index < len(current)):
                current[insert_index] += 1

        values.append(current)

    fig = go.Figure(data=go.Heatmap(
        z=values,
        x=dates,
        y=users,
        colorscale='Viridis'))

    fig.update_layout(
        title='Messages per %d days' % granularity,
        xaxis_nticks=35)

    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    fig.write_html("graphs/messages_per_week.html")

def print_embeds_data():
    headers = ["User", "Total", "Attachments", "Images", "Videos", "Links"]
    result = []
    for username in embeds:
        attachments = 0 if not username in attachment_counts else attachment_counts[username]
        images = 0 if not username in image_counts else image_counts[username]
        videos = 0 if not username in video_counts else video_counts[username]
        links = 0 if not username in link_counts else link_counts[username]
        total = embeds[username]

        if total == 0:
            continue

        result.append([username, total, attachments, images, videos, links])

    result.sort(key=lambda x: x[1], reverse=True)

    print(tabulate(result, headers=headers,tablefmt="fancy_grid"))

def print_avg_comment_length():
    items = {}
    for channel in messages:
        for message in messages[channel]:
            user = message["author"]["username"]
            if not user in items:
                items[user] = []
            
            if message["content"]:
                items[user].append(len(message["content"]))
    
    headers = ["User", "Mean", "Median"]
    result = []
    for user in items:
        if len(items[user]) < 100 or user == "Rythm":
            continue
        result.append([user, np.mean(items[user]), np.median(items[user])])

    result.sort(key=lambda x: x[1], reverse=True)

    print(tabulate(result, headers=headers, tablefmt="fancy_grid"))

print_avg_comment_length()
# show_messages_by_date()
# show_time_graph("Cyber Jockey")
# print_embeds_data()
# print_reaction_data()
# print_reaction_totals()
# show_reaction_graph("reddit_downvote")