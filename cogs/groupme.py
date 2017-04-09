#!/usr/bin/env python3

import re
import groupy
import asyncio
import hashlib
from discord import Embed
from discord.ext import commands
from cogs.utils.config import Config
from cogs.utils import format as formatter

colours = [0x1f8b4c, 0xc27c0e, 0x3498db, 0x206694, 0x9b59b6,
           0x71368a, 0xe91e63, 0xe67e22, 0xf1c40f, 0x1abc9c,
           0x2ecc71, 0xa84300, 0xe74c3c, 0xad1457, 0x11806a]

groupme_objects = {}

class GroupMe:
  def __init__(self, bot):
    self.conf     = Config('configs/groupme.json')
    self.bot      = bot
    self.loop     = bot.loop
    self.l_bots   = []
    self.g_bots   = {}
    self.g_groups = {}
    self.d_chans  = {}

    if 'g_old' not in self.conf:
      self.conf['g_old'] = {}
    if 'links' not in self.conf:
      self.conf['links'] = {}
    if 'key' not in self.conf or not self.conf['key']:
      self.conf['key'] = input('Please enter your GroupMe api key: ').strip()

    if not self.conf['key']:
      raise RuntimeError('No groupme key provied')

    self.conf.save()

    groupy.config.API_KEY = self.conf['key']

    for discord_chan_id in self.conf['links']:
      for g_id in self.conf['links'][discord_chan_id]:
        group, g_bot = self.get_group_bot(g_id)

        #print('linked discord({}) to groupme({})'.format(discord_chan_id,g_id))

        if not group:
          #print('could not find group')
          continue

        channel = self.bot.get_channel(discord_chan_id)
        if not channel:
          #print('error chan')
          continue

        if g_id not in self.g_groups:
          #print('new g_groups: {} -> {}'.format(g_id, str(group)))
          self.l_bots.append(g_bot)
          self.g_groups[g_id] = group

        if channel.id in self.g_bots:
          self.g_bots[channel.id].append(g_bot)
          #print('append g_bots: {}'.format(str(self.g_bots)))
        else:
          self.g_bots[channel.id] = [g_bot]
          #print('new g_bots: {}'.format(str(self.g_bots)))

        if g_id in self.d_chans:
          self.d_chans[g_id].append(channel)
        else:
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

    if channel.id in self.g_bots:
      self.g_bots[channel.id].append(g_bot)
      self.conf['links'][channel.id].append(g_id)
    else:
      self.g_bots[channel.id] = [g_bot]
      self.conf['links'][channel.id] = [g_id]

    if g_id in self.d_chans:
      self.d_chans[g_id].append(channel)
    else:
      self.d_chans[g_id] = [channel]

    if g_id not in self.g_groups:
      self.conf['g_old'][g_id] = None

    self.conf.save()

    await self.bot.say(formatter.ok())

  async def link_from_discord(self, message):
    if message.author.bot:
      return

    if message.content.startswith('.add_groupme_link'):
      return

    try:
      g_bots = self.g_bots[message.channel.id]
      text  = u'<\u200b{}> {}'.format(message.author.name, message.content)
      for a in message.attachments:
        text += '\n{}'.format(str(a)) #TODO - I *think* attachments are strs
      for g_bot in g_bots:
        await self.loop.run_in_executor(None, g_bot.post, text)
    except:
      #print(self.g_bots)
      pass

  async def link_from_groupme(self, message, channels):
    try:
      #print('      send g->d - get text')
      text = message.text if message.text else ''

      name_hash = hashlib.md5()
      name_hash.update(str(message.name).strip().encode())
      name_hash = int(name_hash.hexdigest(), 16)
      #print('      send g->d - get color (\"{}\" -> {} % {} = {:02X})'.format(\
      #         str(message.name).strip(),
      #         name_hash,
      #         len(colours),
      #         colours[name_hash % len(colours)]
      #))
      c = colours[name_hash % len(colours)]

      #print('      send g->d - create embed')
      em = Embed(colour=c)

      #print('      send g->d - get attach')
      for a in message.attachments:
        #print('        attach process')
        if type(a) == groupy.object.attachments.Location:
          text += '\n[{} - ({}, {})]'.format(a.name, a.lat, a.lng)
        elif type(a) == groupy.object.attachments.Image:
          #print('        image: {}'.format(str(a.url)))
          text += '\n[{}]'.format(a.url)
          #em.set_image(str(a.url))
        elif type(a) == groupy.object.attachments.Mentions:
          pass #TODO at some point?
        elif type(a) == groupy.object.attachments.Emoji:
          pass #TODO maybe when their doc explain how this works

      #print('      send g->d - set author: {} [{}]'.format(str(message.name),
      #                                               str(message.avatar_url)
      #))
      if message.avatar_url:
        em.set_author(name=str(message.name), icon_url=str(message.avatar_url))
      else:
        em.set_author(name=str(message.name))

      em.description = text

      #print('      send g->d - send embed to channel(s)')
      for channel in channels:
        #print('        sending {} to {}'.format(str(em), str(channel)))
        await self.bot.send_message(channel, embed=em)
      #print('      send g->d - all ok')
    except Error as err:
      #print(err)
      pass

  async def poll(self):
    #print('polling')
    for bot in self.l_bots:
      #print('  group: {}'.format(str(self.g_groups[bot.group_id])))
      messages = []
      channels = self.d_chans[bot.group_id]

      try:
        #print('    p refresh')
        self.g_groups[bot.group_id].refresh()
        all_messages = self.g_groups[bot.group_id].messages()

        #print('    p splice')
        for message in all_messages:
          #print('      check 1')
          if message.id == self.conf['g_old'][bot.group_id]:
            break
          #print('      check 2')
          if not message.text or not message.text.startswith(u'<\u200b'):
            messages.append(message)

        #print('    p save progress')
        if len(all_messages) > 0:
          self.conf['g_old'][bot.group_id] = all_messages.newest.id
          self.conf.save()

        #print('    p send')
        for message in reversed(messages):
          await self.link_from_groupme(message, channels)
      except:
        #print('    polling failed')
        pass

    #print('    p wait')
    await asyncio.sleep(5 if messages else 25)
    #print('    p queue')
    if self.bot.user.id in groupme_objects and \
       groupme_objects[self.bot.user.id] == self:
         self.loop.create_task(self.poll())
    else:
      #print('cannot poll, must end')
      pass

  def get_group_bot(self, g_id):
    group = None
    g_bot = None

    for g in groupy.Group.list():
      if str(g.id) == str(g_id):
        group = g
        #break

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
  #print('tearing down')
  del groupme_objects[bot.user.id]

def setup(bot):
  g = GroupMe(bot)
  groupme_objects[bot.user.id] = g
  bot.add_listener(g.link_from_discord, "on_message")
  bot.add_cog(g)
