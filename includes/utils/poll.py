#!/usr/bin/env python3

import re
import discord
import asyncio
import logging
import time
import cogs.utils.heap as heap
import cogs.utils.format as formatter

logger = logging.getLogger('navi.poll')

class Poll(heap.HeapNode):
  def __init__(self, question, opts, channel, sleep, timeout=0):
    self.options    = {}
    self.question   = question
    self.channel_id = getattr(channel, 'id', channel)
    self.end_time   = timeout if timeout else sleep + time.time()

    for opt in opts:
      self.options[opt] = set()

  @staticmethod
  def from_dict(dct):
    question   = dct.get('question')
    options    = dct.get('options')
    channel_id = dct.get('channel_id')
    end_time   = dct.get('end_time')

    return Poll(question, options, channel_id, 0, end_time)

  def to_dict(self):
    return {
      '__poll__'   : True,
      'question'   : self.question,
      'options'    : self.options,
      'channel_id' : self.channel_id,
      'end_time'   : self.end_time
    }

  # ==
  def __eq__(self, other):
    return type(self)      == type(other)   and \
           self.channel_id == other.channel_id

  # <
  def __lt__(self, other):
    return self.end_time < other.end_time

  # >
  def __gt__(self, other):
    return self.end_time > other.end_time

  async def begin(self, bot):
    message = 'Poll stated: \"{}\"\n{}'.format(self.question,
                                               '\n'.join(self.options)
    )
    await bot.say(formatter.escape_mentions(message))

  async def end(self, bot):
    chan = bot.get_channel(self.channel_id)
    await bot.send_message(chan, formatter.escape_mentions(self.results()))

  def vote(self, user : discord.User, message):
    v = False
    for i in self.options:
      if not v and re.search(r'(?i)\b{}\b'.format(i), message):
        self.options[i].add(user.id)
        v = True
      elif user.id in self.options[i]:
        self.options[i].remove(user.id)

  def results(self):
    out = ''
    formatting = '{{:<{}}} - {{:>{}}}\n'
    longest = [0, 0]

    for i in self.options:
      if len(i) > longest[0]:
        longest[0] = len(i)
      if len(str(len(self.options[i]))) > longest[1]:
        longest[1] = len(str(len(self.options[i])))

    formatting = formatting.format(*longest)
    for i in self.options:
      out += formatting.format(i, len(self.options[i]))

    return '**{}**:\n'.format(self.question) + formatter.code(out[:-1])
