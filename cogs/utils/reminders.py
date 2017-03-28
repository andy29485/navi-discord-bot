#!/usr/bin/env python3

import re
import time

class Reminder:
  def __init__(self, channel_id, user_id, message, end_time=0):
    self.channel_id = channel_id
    self.user_id    = user_id
    self.message    = message
    self.end_time   = end_time
    if not end_time:
      self.parse_time()

  def is_ready(self):
    return self.end_time <= time.time()

  def get_message(self):
    return '{}: {}'.format(self.user_id, self.message)

  def parse_time(self):
    offset = time.time()
    times = {
             '(?i)(\\d+)\\s*s(econds?)?'    : 1,
             '(?i)(\\d+)\\s*m(in(ute)?s?)?' : 60,
             '(?i)(\\d+)\\s*h(ours?)?'      : 360,
             '(?i)(\\d+)\\s*d(ays?)?'       : 8640,
             '(?i)(\\d+)\\s*w(eeks?)?'      : 60480,
             '(?i)(\\d+)\\s*months?'        : 254016
    }
    for t in times:
      match = re.search(t, self.message)
      self.message = re.sub(t, '', self.message).strip()
      if match:
        offset += times[t]*float(match.group(1))
    self.end_time = offset

  def to_dict(self):
    dct = {'__reminder__':'true'}
    dct['channel_id'] = self.channel_id
    dct['user_id']    = self.user_id
    dct['message']    = self.message
    dct['end_time']   = self.end_time
    return dct

  def insertInto(self, into):
    if not into or self.end_time > into[-1].end_time:
      into.append(self)
      return
    lo = 0
    hi = len(into)
    while lo < hi:
      mid = (lo+hi)//2
      if self.end_time > into[mid].end_time:
        hi = mid
      else:
        lo = mid+1
    into.insert(lo, self)
