from threading import Lock, Thread
from queue import Queue
import sys
import json
import os
import time
import numpy as np
from terminal import Terminal, Colors
import requests
import math

class DiscordDownloader:
  def __init__(self, headers: dict, server: dict, threads: int, maxAttempts: int = 20, downloadReactions = True):
    self.headers = headers
    self.terminalLock = Lock()
    self.messages = {}
    self.server = server
    self.todo = Queue()
    self.threads = threads
    self.maxAttempts = maxAttempts
    self.discordApiUrl = "https://discord.com/api/v8"
    self.downloadReactions = downloadReactions
    self.shouldStop = False

  def try_get(self, url: str, threadId: int, params: dict = None):
    response = requests.get(url = url, params = params, headers = self.headers)

    attempts = 0
    while attempts < self.maxAttempts and not self.shouldStop:
      if response.status_code == requests.codes.too_many:
        Terminal.setStatus(self.terminalLock, threadId, f"Thread {threadId} - [TOO_MANY]", Colors.BG_RED, Colors.FG_RED)
        result = response.json()
        sleep_time = int(math.ceil(float(result["retry_after"]) / 1000))
        if sleep_time <= 0:
          sleep_time = 10
        time.sleep(sleep_time)
        attempts += 1
        continue
      elif response.status_code == requests.codes.forbidden:
        Terminal.setStatus(self.terminalLock, threadId, f"Thread {threadId} - [FORBIDDEN]", Colors.BG_BRIGHT_RED, Colors.BG_BRIGHT_RED)
        return None
      elif response.status_code != requests.codes.ok:
        Terminal.setStatus(self.terminalLock, threadId, f"Thread {threadId} - [{response.status_code}]", Colors.BG_RED, Colors.FG_RED)
        time.sleep(10)
        attempts += 1
        continue
      else:
        Terminal.setStatus(self.terminalLock, threadId, f"Thread {threadId} - [OK]", Colors.BG_GREEN, Colors.FG_GREEN)
        return response.json()
    
    Terminal.setStatus(self.terminalLock, threadId, f"Thread {threadId} - Exceeded attempts", Colors.BG_BRIGHT_RED, Colors.BG_BRIGHT_RED)
    return None

  def get_reactions(self, channel: str, message: str, emoji: str, threadId: int):
    return self.try_get(f"{self.discordApiUrl}/channels/{channel}/messages/{message}/reactions/{emoji}", threadId)

  def get_messages(self, channel: str, threadId: int, before: str = None):
    params = {"limit": "100"}
    if before: params["before"] = before

    response = self.try_get(f"{self.discordApiUrl}/channels/{channel}/messages", threadId, params)

    if not response:
      return []

    for message in response:
      if not "reactions" in message:
        continue

      if self.downloadReactions:
        for reaction in message["reactions"]:
          if self.shouldStop:
            break
          if reaction["emoji"]["id"]:
            reaction["users"] = self.get_reactions(channel, message["id"], reaction["emoji"]["name"] + "%3A" + reaction["emoji"]["id"], threadId)
          else:
            reaction["users"] = self.get_reactions(channel, message["id"], reaction["emoji"]["name"], threadId)

    return response

  def start(self):
    for channel in self.server["channels"]:
      self.todo.put(channel)

    with Terminal() as t:
      try:
        threads = [Thread(target = self.downloader, args = [i]) for i in range(1, self.threads + 1)]
        for t in threads: t.start() # Start all the threads
        for t in threads: t.join() # Wait for all threads to finish
      except KeyboardInterrupt:
        self.shouldStop = True
        Terminal.setStatus(self.terminalLock, self.threads + 5, f"Waiting for threads to finish", Colors.BG_MAGENTA, Colors.FG_MAGENTA)

  def downloader(self, id):
    last_result_bad = False
    while self.todo.not_empty and not self.shouldStop:
      last_result_bad = False
      channel = self.todo.get()
      channel_name = channel["name"]

      self.messages[channel_name] = []

      result = self.get_messages(channel["id"], id)
      before = None
      while len(result) > 0 and not self.shouldStop:
        self.messages[channel_name].extend(result)
        lastMsg = result[len(result) - 1]
        before = lastMsg["id"]
        result = self.get_messages(channel["id"], id, before)
      
      if len(self.messages[channel_name]) == 0:
        self.messages[channel_name] = "Unable to download any messages for this channel"
        last_result_bad = True
    
    if not last_result_bad:
      Terminal.setStatus(self.terminalLock, id, f"Thread {id} - [Finished]", Colors.BG_BRIGHT_GREEN, Colors.FG_BRIGHT_GREEN)

if __name__ == "__main__":
  if not os.path.exists("private.json"):
    sys.stderr.write("Missing required input file: private.json")
    exit(1)
  
  if not os.path.exists("server.json"):
    sys.stderr.write("Missing required input file: server.json")
    exit(1)

  with open("private.json") as f:
    private = json.load(f)
  
  with open("server.json") as f:
    server = json.load(f)

  downloader = DiscordDownloader(headers = private, server = server, threads = 16)
  downloader.start()