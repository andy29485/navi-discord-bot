#!/usr/bin/env python3

import re
import groupy
import asyncio
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
      group, bot = self.get_group_bot(g_id)

      if not group:
        continue

      channel = self.bot.get_channel(discord_chan_id)

      self.d_chans[channel] = g_bot
      self.g_bots[g_bot]    = channel
      self.g_old[g_id]      = None
      self.g_groups[g_id]   = group

    self.loop.create_task(self.poll())


  @commands.command()
  async def add_groupme_link(self, *, g_id : str):
    group, bot = self.get_group_bot(g_id)

    if not group:
      await self.bot.say(formatter.error("I am not in a group with that id"))
      return

    channel = ctx.message.channel

    self.conf['links'][channel.id] = g_id

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

  async def poll(self):
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

    await asyncio.sleep(15)
    self.loop.create_task(self.poll())

  def get_group_bot(self, g_id):
    group = None
    g_bot = None

    for g in groupy.Group.list():
      if str(g.id) == str(g_id):
        group = g
        break

    if not group:
      return None, None

    for bot in groupy.Bot.list():
      if str(bot.group_id) == str(g_id):
        g_bot = bot
        break

    if not g_bot:
      g_bot = groupy.Bot.create('Navi', group,
                                avatar_url=self.bot.user.avatar_url
      )
    return group, g_bot

def setup(bot):
  g = General(bot)
  bot.add_listener(g.link_from_discord, "on_message")
  bot.add_cog(g)

