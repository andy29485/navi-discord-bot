#!/usr/bin/env python3

import re
import time
import datetime
import cogs.utils.heap as heap
from cogs.utils.format import ok
from cogs.utils import discord_helper as dh

class Reminder(heap.HeapNode):
  def __init__(self, channel_id, user_id, message, end_time=0):
    self.user_id    = getattr(user_id,    'id',    user_id)
    self.channel_id = getattr(channel_id, 'id', channel_id)
    self.message    = message
    self.end_time   = end_time

    if not end_time:
      self.parse_time()

  @staticmethod
  def from_dict(dct):
    chan     = dct.get('channel_id')
    mesg     = dct.get('message')
    user     = dct.get('user_id')
    end_time = dct.get('end_time')

    return Reminder(constr, chan, user, mesg, end_time)

  def to_dict(self):
    dct = {'__reminder__':'true'}
    dct['channel_id'] = self.channel_id
    dct['user_id']    = self.user_id
    dct['message']    = self.message
    dct['end_time']   = self.end_time
    return dct

  # ==
  def __eq__(self, other):
    return type(self)      == type(other)      and \
           self.role_id    == other.role_id    and \
           self.channel_id == other.channel_id and \
           self.message    == other.message    and \
           self.user_id    == other.user_id

  # <
  def __lt__(self, other):
    return self.end_time < other.end_time

  # >
  def __gt__(self, other):
    return self.end_time > other.end_time

  async def begin(self, bot):
    t = datetime.datetime.fromtimestamp(self.end_time).isoformat()
    await bot.say(ok(f'Will remind you at {t}'))

  async def end(self, bot):
    chan = bot.get_channel(self.channel_id)
    await  bot.send_message(chan, self.get_message())

  def get_message(self):
    return '{}: {}'.format(self.user_id, self.message)

  def parse_time(self):
    self.end_time, self.message = dh.get_end_time(self.message)
