from threading import Lock
import sys

class Colors:
  FG_BLACK = 30
  FG_RED = 31
  FG_GREEN = 32
  FG_YELLOW = 33
  FG_BLUE = 34
  FG_MAGENTA = 35
  FG_CYAN = 36
  FG_WHITE = 37
  FG_EXTENDED = 38
  FG_DEFAULT = 39
  BG_BLACK = 40
  BG_RED = 41
  BG_GREEN = 42
  BG_YELLOW = 43
  BG_BLUE = 44
  BG_MAGENTA = 45
  BG_CYAN = 46
  BG_WHITE = 47
  BG_EXTENDED = 48
  BG_DEFAULT = 49
  FG_BRIGHT_BLACK = 90
  FG_BRIGHT_RED = 91
  FG_BRIGHT_GREEN = 92
  FG_BRIGHT_YELLOW = 93
  FG_BRIGHT_BLUE = 94
  FG_BRIGHT_MAGENTA = 95
  FG_BRIGHT_CYAN = 96
  FG_BRIGHT_WHITE = 97
  BG_BRIGHT_BLACK = 100
  BG_BRIGHT_RED = 101
  BG_BRIGHT_GREEN = 102
  BG_BRIGHT_YELLOW = 103
  BG_BRIGHT_BLUE = 104
  BG_BRIGHT_MAGENTA = 105
  BG_BRIGHT_CYAN = 106
  BG_BRIGHT_WHITE = 107

class Terminal:
  @staticmethod
  def setColor(fg, bg):
    return lambda: sys.stdout.write(f"\033[{fg};{bg}m")

  @staticmethod
  def setPos(x, y):
    return lambda: sys.stdout.write(f"\033[{y};{x}H")

  @staticmethod
  def write(s):
    return lambda: sys.stdout.write(s)

  @staticmethod
  def writeCenter(s, l):
    padL = int((l - len(s)) / 2)
    padR = len(s) % 2 == 0 and padL or int((l - len(s)) / 2) - 1
    return lambda: sys.stdout.write(" " * padL + s + " " * padR)
  
  @staticmethod
  def setStatus(lock: Lock, y: int, text: str, bg: int, fg: int):
    commands = [
      Terminal.setPos(1, y),
      Terminal.setColor(fg, Colors.BG_DEFAULT),
      Terminal.write("[ "),
      Terminal.setColor(Colors.FG_BLACK, bg),
      Terminal.writeCenter(text, 45),
      Terminal.setColor(fg, Colors.BG_DEFAULT),
      Terminal.write(" ]")
    ]

    with lock:
      for f in commands:
        f()
        sys.stdout.flush()
  
  @staticmethod
  def useAlternateBuffer():
    sys.stdout.write("\033[?1049h") # Use alternate screen buffer
    sys.stdout.write("\033[2J") # Clear the screen
    sys.stdout.write("\033[?25l") # Hide the cursor
  
  @staticmethod
  def useDefaultBuffer():
    sys.stdout.write("\033[?1049l") # Stop using alternate screen buffer
    sys.stdout.write("\033[?25h") # Unhide the cursor