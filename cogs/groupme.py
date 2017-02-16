#!/usr/bin/env python3

import re
import asyncio
from groupy import Bot, Group
from discord.ext import commands
from .utils.config import Config
from .utils import format as formatter

class General:
  def __init__(self, bot):
    self.conf    = Config('configs/groupme.json')
    self.bot     = bot
    self.loop    = bot.loop
    self.g_bots  = {}
    self.g_old   = {}
    self.d_chans = {}

    groupy.config.API_KEY = self.conf['key']

    for discord_chan_id in self.conf['links']:
      g_id    = self.conf['links'][discord_chan_id]
      group   = None

      for g in Group.list():
        if g.id == g_id:
          group = g
          break
      if not group:
        continue

      g_bot   = Bot.create('Navi', group, image_url=self.bot.user.avatar_url)
      channel = self.bot.get_channel(discord_chan_id)

      self.d_chans[channel] = g_bot
      self.g_bots[g_bot]    = channel
      self.g_old[g_id]      = None
      self.g_groups[g_id]   = group

    self.loop.call_soon(self.poll)
    #TODO {'28986169':''}


  @commands.command(pass_context=True)
  async def add_groupme_link(self, ctx):
    g_id  = ctx.message.content
    group = None

    for g in Group.list():
      if g.id == g_id:
        group = g
        break
    if not group:
      await self.bot.say(formatter.error("I am not in a group with that id"))

    g_bot   = Bot.create('Navi', group, image_url=self.bot.user.avatar_url)
    channel = ctx.message.channel

    self.d_chans[channel] = g_bot
    self.g_bots[g_bot]    = channel
    self.g_old[g_id]      = None
    self.g_groups[g_id]   = group

    await self.bot.say(formatter.ok())

  async def link_from_discord(self, message):
    if message.author.bot:
      return

    try:
      g_bot = self.d_chans[message.channel]
      text  = '<{}> {}'.format(message.author.nick, message.content)
      await loop.run_in_executor(None, g_bot.post, text)
    except:
      pass


  async def link_from_groupme(self, message, channel):
    try:
      text = '<{}> {}'.format(message.name, message.text)
      await self.bot.send_message(channel, text)
    except:
      pass

  async def poll()
    for bot in self.g_bots():
      messages     = []
      all_messages = self.g_groups[bot.group_id].messages()
      for message in all_messages:
        if message.id == self.g_old[bot]:
          break
        messages.append(message)
      if len(all_messages) > 0:
        self.g_old[bot] = all_messages[0].id
      for message in reversed(messages):
        await self.link_from_groupme(message, self.g_bots[bot])

    self.loop.call_later(15, self.poll)

def setup(bot):
  g = General(bot)
  bot.add_listener(g.link_from_discord, "on_message")
  bot.add_cog(g)

