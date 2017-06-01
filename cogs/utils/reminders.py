#!/usr/bin/env python3

import re
import time
import cogs.utils.heap as heap
from dateutil import parser

class Reminder:
  def __init__(self, channel_id, user_id, message, end_time=0):
    self.channel_id = channel_id
    self.user_id    = user_id
    self.message    = message
    self.end_time   = end_time
    if not end_time:
      self.parse_time()

  def __lt__(self, other):
    return self.end_time < other.end_time

  def __gt__(self, other):
    return self.end_time > other.end_time

  def is_ready(self):
    return self.end_time <= time.time()

  def get_message(self):
    return '{}: {}'.format(self.user_id, self.message)

  def __repr__(self):
    return str(self.end_time)

  def parse_time(self):
    offset = time.time()
    times = {
         '(?i)(\\d+)\\s*s(econds?)?'    : 1,
         '(?i)(\\d+)\\s*m(in(ute)?s?)?' : 60,
         '(?i)(\\d+)\\s*h(ours?)?'      : 3600,
         '(?i)(\\d+)\\s*d(ays?)?'       : 86400,
         '(?i)(\\d+)\\s*w(eeks?)?'      : 604800,
         '(?i)(\\d+)\\s*months?'        : 2628000
    }
    if re.search(r'(?i)^(me)?\s*in', self.message):
      offset = parser.parse(self.message).timestamp()
    for t in times:
      match = re.search(t, self.message)
      self.message = re.sub(t, '', self.message).strip()
      if match:
        offset += times[t]*float(match.group(1))
    self.message = re.sub(r'(?i)^(me\s+)?(at|in)?\s*', '', self.message).strip()
    self.end_time = offset

  def to_dict(self):
    dct = {'__reminder__':'true'}
    dct['channel_id'] = self.channel_id
    dct['user_id']    = self.user_id
    dct['message']    = self.message
    dct['end_time']   = self.end_time
    return dct

  def insertInto(self, values):
    heap.insertInto(values, self)

  def popFrom(self, values):
    return heap.popFrom(values)
