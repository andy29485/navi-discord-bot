#!/usr/bin/env python3

# This file contains "aliases" for discord formats
#   this way the message for successful commands will be the same
#   the names of the methods should make it evident whay they do

def error(text):
  return f"{{NO ENTRY SIGN}} {text}"

def warning(text):
  return f"{{WARNING SIGN}} {text}"

def info(text):
  return f"{{INFORMATION SOURCE}} {text}"

def ok(text=''):
  return f"{{OK HAND SIGN}} {text}"

def question(text):
  return f"{{BLACK QUESTION MARK ORNAMENT}} {text}"

def bold(text):
  return f"**{text}**"

def code(text, lang=""):
  return f"```{lang}\n{text}\n```"

def inline(text):
  return f"`{text}`"

def italics(text):
  return f"*{text}*"

def strikethrough(text):
  return f"~~{text}~~"

def underline(text):
  return f"__{text}__"

def escape_mentions(text):
  '''
  removes mentiones by adding a zero-width space after the '@'
  '''
  return text.replace('@', '@\u200b')

def escape(text, mentions=False):
  '''
  escapes discord messages by replacing meaningful symbols
  it will also replace mentions if "mentions" is True
  '''
  if mentions:
    text = escape_mentions(text)
  text = text.replace("`", "\\`") \
             .replace("*", "\\*") \
             .replace("_", "\\_") \
             .replace("~", "\\~")
  return text
