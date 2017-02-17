#!/usr/bin/env python3

import re
import groupy
import asyncio
from discord.ext import commands
from .utils.config import Config
from .utils import format as formatter

class GroupMe:
  def __init__(self, bot):
    self.conf     = Config('configs/groupme.json')
    self.bot      = bot
    self.loop     = bot.loop
    self.l_bots   = []
    self.g_bots   = {}
    self.d_chans  = {}
    self.g_groups = {}

    groupy.config.API_KEY = self.conf['key']

    for serv_id in self.conf['links']:
      server  = self.bot.get_server(serv_id)
      if not server:
        print('error serv')
        continue
      for discord_chan_id in self.conf['links'][serv_id]:
        g_id            = self.conf['links'][serv_id][discord_chan_id][0]
        group, g_bot    = self.get_group_bot(g_id)

        if not group:
          continue

        channel = server.get_channel(discord_chan_id)
        if not server:                                                                                                                                   
          print('error chan')
          continue
        print('chan: ' + 'err' if not channel else 'ok')

        self.l_bots.append(g_bot)
        self.d_chans[channel] = g_bot
        self.g_bots[g_id]     = [server, channel]
        self.g_groups[g_id]   = group

    self.loop.create_task(self.poll())


  @commands.command(pass_context=True)
  async def add_groupme_link(self, ctx, g_id : str):
    group, g_bot = self.get_group_bot(g_id)

    if not group:
      await self.bot.say(formatter.error("I am not in a group with that id"))
      return

    channel = ctx.message.channel
    server  = channel.server

    if channel.server.id not in self.conf['links']:
      self.conf['links'][channel.server.id] = {}
    self.conf['links'][channel.server.id][channel.id] = [g_id, None]
    self.conf.save()

    self.l_bots.append(g_bot)
    self.d_chans[channel] = g_bot
    self.g_bots[g_id]     = [server, channel]
    self.g_groups[g_id]   = group

    await self.bot.say(formatter.ok())

  async def link_from_discord(self, message):
    if message.author.bot:
      return

    if message.content.startswith('.add_groupme_link'):
      return

    try:
      g_bot = self.d_chans[message.channel]
      text  = '<{}> {}'.format(message.author.name, message.content)
      await self.loop.run_in_executor(None, g_bot.post, text)
    except:
      pass

  async def link_from_groupme(self, message, channel):
    try:
      text = '<{}> {}'.format(message.name, message.text)
      await self.bot.send_message(channel, text)
    except:
      pass

  async def poll(self):
    for bot in self.l_bots:
      messages = []
      server  = self.g_bots[bot.group_id][0]
      channel = self.g_bots[bot.group_id][1]

      self.g_groups[bot.group_id].refresh()
      all_messages = self.g_groups[bot.group_id].messages()

      for message in all_messages:
        if message.id == self.conf['links'][server.id][channel.id][1]:
          break
        if not message.text.startswith("<"):
          messages.append(message)

      if len(all_messages) > 0:
        self.conf['links'][server.id][channel.id][1] = all_messages.newest.id
        self.conf.save()

      for message in reversed(messages):
        await self.link_from_groupme(message, channel)

    await asyncio.sleep(4)
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
  g = GroupMe(bot)
  bot.add_listener(g.link_from_discord, "on_message")
  bot.add_cog(g)
