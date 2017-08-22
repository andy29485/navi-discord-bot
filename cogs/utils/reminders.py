#!/usr/bin/env python3

import re
import time
import cogs.utils.heap as heap
from cogs.utils import discord_helper as dh

class Reminder:
  def __init__(self, channel_id, user_id, message, end_time=0):
    self.user_id    = getattr(user_id,    'id',    user_id)
    self.channel_id = getattr(channel_id, 'id', channel_id)
    self.message    = message
    self.end_time   = end_time

    if not end_time:
      self.parse_time()

  def __lt__(self, other):
    return self.end_time < other.end_time

  def __gt__(self, other):
    return self.end_time > other.end_time

  @property
  def time_left(self):
    return self.end_time - time.time()

  def get_message(self):
    return '{}: {}'.format(self.user_id, self.message)

  def __repr__(self):
    return str(self.end_time)

  def parse_time(self):
    self.end_time, self.message = dh.get_end_time(self.message)

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
