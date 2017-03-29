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

  def __lt__(self, other):
    return self.end_time < other.end_time

  def __gt__(self, other):
    return self.end_time > other.end_time

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

  def insertInto(self, values):
    i = len(values)
    values.append(self)
    pushUp(values, i)

  def popFrom(self, values):
    largest   = values[0]
    values[0] = values.pop()
    pushDown(values, 0, len(values))
    return largest


def pushUp(values, index, first = 0):
  parent = (index-1)//2;

  while index >= first and values[index] > values[parent]:
    values[index], values[parent] = values[parent], values[index];

    index  = parent;
    parent = (index-1)//2;

def pushDown(values, index, last = 0):
  if not last:
    last = len(values)

  left    = 2*index + 1;
  right   = 2*index + 2;
  largest = index;

  largest = largest if (left> last or values[largest]>values[left])  else left
  largest = largest if (right>last or values[largest]>values[right]) else right

  if largest != index:
    values[largest], values[index] = values[index], values[largest]
    pushDown(values, largest, last)
