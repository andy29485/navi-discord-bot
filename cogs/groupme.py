#!/usr/bin/env python3

import re
import groupy
import asyncio
from discord.ext import commands
from .utils.config import Config
from .utils import format as formatter

colours = [0x1abc9c, 0x11806a, 0x2ecc71, 0x1f8b4c, 0x3498db, 0x206694,
           0x9b59b6, 0x71368a, 0xe91e63, 0xad1457, 0xf1c40f, 0xc27c0e,
           0xe67e22, 0xa84300, 0xe74c3c, 0x992d22]

groupme_objects = {}

class GroupMe:
  def __init__(self, bot):
    self.conf     = Config('configs/groupme.json')
    self.bot      = bot
    self.loop     = bot.loop
    self.l_bots   = []
    self.g_bots   = {}
    self.d_chans  = {}
    self.g_groups = {}


    if 'g_old' not in self.conf:
      self.conf['g_old'] = {}
    if 'links' not in self.conf:
      self.conf['links'] = {}
    if 'key' not in self.conf:
      self.conf['key'] = input('please enter your GroupMe api key ')
    self.conf.save()
    
    groupy.config.API_KEY = self.conf['key']

    for discord_chan_id in self.conf['links']:
      g_id         = self.conf['links'][discord_chan_id]
      group, g_bot = self.get_group_bot(g_id)

      if not group:
        continue

      channel = self.bot.get_channel(discord_chan_id)
      if not channel:                                                                                                                                   
        print('error chan')
        continue

      if g_id not in self.g_groups:
        self.l_bots.append(g_bot)
        self.g_groups[g_id] = group

      if channel_id in self.g_bots:
        self.g_bots[channel_id].append(g_bot)
      else
        self.g_bots[channel_id] = [g_bot]

      if g_id in self.d_chans:
        self.d_chans[g_id].append(channel)
      else
        self.d_chans[g_id] = [channel]

    self.loop.create_task(self.poll())


  @commands.command(pass_context=True)
  async def add_groupme_link(self, ctx, g_id : str):
    channel = ctx.message.channel
    group, g_bot = self.get_group_bot(g_id)

    if not group:
      await self.bot.say(formatter.error("I am not in a group with that id"))
      return

    if g_id not in self.g_groups:
      self.l_bots.append(g_bot)
      self.g_groups[g_id] = group

    if channel_id in self.g_bots:
      self.g_bots[channel_id].append(g_bot)
      self.conf['links'][channel_id].append(g_id)
    else
      self.g_bots[channel_id] = [g_bot]
      self.conf['links'][channel_id] = [g_id]

    if g_id in self.d_chans:
      self.d_chans[g_id].append(channel)
    else
      self.d_chans[g_id] = [channel]
      self.conf['g_old'][g_id] = None

    self.conf.save()

    await self.bot.say(formatter.ok())

  async def link_from_discord(self, message):
    if message.author.bot:
      return

    if message.content.startswith('.add_groupme_link'):
      return

    try:
      g_bots = self.g_bots[message.channel]
      text  = u'<\u200b{}> {}'.format(message.author.name, message.content)
      for a in message.attachments:
        text += '\n{}'.format(str(a)) #TODO - I *think* attachments are strs
      for g_bot in g_bots:
        await self.loop.run_in_executor(None, g_bot.post, text)
    except:
      pass

  async def link_from_groupme(self, message, channels):
    try:
      text = message.text
      for a in message.attachments:
        if type(a) == groupy.object.attachments.Location:
          text += '\n[{} - ({}, {})]'.format(a.name, a.lat, a.lng)
        elif type(a) == groupy.object.attachments.Image:
          text += '\n[{}]'.format(a.url)
        elif type(a) == groupy.object.attachments.Mentions:
          pass #TODO at some point?
        elif type(a) == groupy.object.attachments.Emoji:
          pass #TODO maybe when their doc explain how this works

      c = colours[message.name.__hash__() % len(colours)]

      em = discord.Embed(title='', description=text, colour=c)
      em.set_author(name=message.name, icon_url=messages.avatar_url)
      for channel in channels:
        await self.bot.send_message(channel, embed=em)
    except:
      pass

  async def poll(self):
    for bot in self.l_bots:
      messages = []
      channels = self.d_chans[bot.group_id]

      self.g_groups[bot.group_id].refresh()
      all_messages = self.g_groups[bot.group_id].messages()

      for message in all_messages:
        if message.id == self.conf['g_old'][bot.group_id]:
          break
        if not message.text.startswith(u'<\u200b'):
          messages.append(message)

      if len(all_messages) > 0:
        self.conf['g_old'][bot.group_id] = all_messages.newest.id
        self.conf.save()

      for message in reversed(messages):
        await self.link_from_groupme(message, channels)

    await asyncio.sleep(4)
    if self.bot.id in groupme_objects and groupme_objects[self.bot.id] == self:
      self.loop.create_task(self.poll())
    else:
      print('cannot poll, must end')

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


def teardown(bot):
  del groupme_objects[bot.id]

def setup(bot):
  g = GroupMe(bot)
  groupme_objects[bot.id] = g
  bot.add_listener(g.link_from_discord, "on_message")
  bot.add_cog(g)
