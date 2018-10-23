#!/usr/bin/env python3

import re
import time
import logging
from datetime import datetime
from discord import Message
import includes.utils.heap as heap
from includes.utils.format import ok
from includes.utils import discord_helper as dh

logger = logging.getLogger('navi.reminders')

class Reminder(heap.HeapNode):
  def __init__(self, channel_id, user_id, message,
               end_time=0, times=[],
               command=False, reminder_id=0):
    self.user_id     = int(getattr(user_id,    'id',    user_id))
    self.channel_id  = int(getattr(channel_id, 'id', channel_id))
    self.message     = message
    self.end_time    = end_time
    self.times       = times
    self.command     = command
    self.reminder_id = reminder_id

    if not end_time:
      self.parse_time()

  @staticmethod
  def from_dict(dct):
    user        = int(dct.get('user_id'))
    chan        = int(dct.get('channel_id'))
    mesg        = dct.get('message')
    end_time    = dct.get('end_time')
    times       = dct.get('times', [])
    command     = dct.get('command', False)
    reminder_id = dct.get('reminder_id', 0)

    return Reminder(chan, user, mesg, end_time, times, command, reminder_id)

  def to_dict(self):
    return {
      '__reminder__': True,
      'user_id'     : int(self.user_id),
      'channel_id'  : int(self.channel_id),
      'message'     : self.message,
      'end_time'    : self.end_time,
      'times'       : self.times,
      'command'     : self.command,
      'reminder_id' : self.reminder_id
    }

  # ==
  def __eq__(self, other):
    return type(self)       == type(other)       and \
           self.reminder_id == other.reminder_id

  # <
  def __lt__(self, other):
    return self.end_time < other.end_time

  # >
  def __gt__(self, other):
    return self.end_time > other.end_time

  async def begin(self, ctx):
    t = datetime.fromtimestamp(self.end_time).isoformat().replace('T', ' ')
    if not self.reminder_id:
      while True:
        self.reminder_id = int(time.time()*1000000)%1000000
        for rem in self.heap:
          if self is not rem and self == rem:
            break
        else:
          break
    if ctx:
      async with ctx.typing():
        await ctx.send(ok(f'Will remind you at {t} (id: {self.reminder_id})'))

  async def end(self, bot):
    chan = bot.get_channel(self.channel_id)
    serv = chan and chan.guild
    user = chan and dh.get_user(serv, self.user_id)

    if not chan:
      chan = self.channel_id
      logger.error(f'could not send message \"{self.message}\" to <#{chan}>')
      return

    if self.command:
      member = {
        'id':            int(user.id),
        'username':      user.name,
        'avatar':        user.avatar,
        'discriminator': user.discriminator
      }
      msg = Message(
        content=self.message,
        id=0,
        channel=chan,
        author=member,
        attachments=[],
        reactions=[],
        type=0,
        channel_id=chan.id,
      )
      await bot.process_commands(msg)
    else:
      await chan.send(self.get_message(user))
    if self.times:
      next_rem = Reminder(
        self.channel_id,
        self.user_id,
        self.message,
        0,
        self.times,
        self.command,
        self.reminder_id
      )
      if next_rem.time_left > 600:
        await self.heap.push(next_rem)

  def get_message(self, user):
    return f'{user.mention}: {self.message} (id: {self.reminder_id})'

  def parse_time(self):
    times = ' '.join(self.times)
    self.end_time,message,times = dh.get_end_time(times or self.message)
    self.message = message or self.message

    while True:
      first = self.message.split()[0]
      if first[0] == '-':
        for opt in first[1:]:
          if opt in 'c':
            self.command = True
          elif opt in 'r':
            self.times = times
      else:
        break
      self.message = self.message.replace(first, '', 1).strip()
