#!/usr/bin/env python3

import re
import discord
import asyncio
import cogs.utils.format as formatter

class Poll:
  def __init__(self, bot, channel:discord.Channel, question, options, sleep, p):
    self.options  = {}
    self.question = question
    self.ongoing  = False
    self.bot      = bot
    self.channel  = channel
    self.sleep    = sleep
    self.polls    = p
    
    for opt in options:
      self.options[opt] = set()
  
  def vote(self, user : discord.User, message):
    v = False
    for i in self.options:
      if not v and re.search(r'(?i)\b{}\b'.format(i), message):
        self.options[i].add(user)
        v = True
      elif user in self.options[i]:
        self.options[i].remove(user)
  
  async def start(self):
    message = 'Poll stated: \"{}\"\n{}'.format(self.question,
                                               '\n'.join(self.options))
    await self.bot.say(formatter.escape_mentions(message))
    self.ongoing = True
    await asyncio.sleep(self.sleep)
    if self.ongoing:
      await self.stop()
  
  async def stop(self):
    self.ongoing = False
    await self.bot.say(formatter.escape_mentions(self.results()))
    self.polls.pop(self.channel)
  
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

