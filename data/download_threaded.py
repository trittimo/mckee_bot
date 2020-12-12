from threading import Lock, Thread, Timer
from collections.abc import Callable
from queue import Queue
import sys
import time
import numpy as np
from terminal import Terminal, Colors

class DiscordDownloader:
  def __init__(self, settings: object):
    self.settings = settings
    self.terminalLock = Lock()
    self.messages = {}

  def downloader(self, id):
    self.messages[id] = {}
    for i in range(np.random.randint(5, 10)):
      time.sleep(1)
      status = np.random.choice(2, 1, p = [0.2, 0.8])[0] == 0 and "404" or "200"
      bgCol = status == "404" and Colors.BG_RED or Colors.BG_GREEN
      fgCol = status == "404" and Colors.FG_RED or Colors.FG_GREEN
      Terminal.setStatus(self.terminalLock, id, f"Thread {id} - [{status}]", bgCol, fgCol)

    time.sleep(3)
    Terminal.setStatus(self.terminalLock, id, f"Thread {id} - [Finished]", Colors.BG_BRIGHT_GREEN, Colors.FG_BRIGHT_GREEN)

if __name__ == "__main__":
  downloader = DiscordDownloader({})

  Terminal.useAlternateBuffer()

  threads = [Thread(target = downloader.downloader, args = [i]) for i in range(1, 16)]
  for t in threads: t.start() # Start all the threads
  for t in threads: t.join() # Wait for all threads to finish

  Terminal.useDefaultBuffer()