#!/usr/bin/env python3

from discord.ext import commands
from cogs.utils.config import Config
from cogs.utils.format import *
from cogs.utils.emby_playlist import Player
from discord import Embed
import discord
import asyncio
import hashlib
import logging
from embypy import Emby as EmbyPy
from embypy.objects import EmbyObject
import re
from cogs.utils import puush

colours = [0x1f8b4c, 0xc27c0e, 0x3498db, 0x206694, 0x9b59b6,
           0x71368a, 0xe91e63, 0xe67e22, 0xf1c40f, 0x1abc9c,
           0x2ecc71, 0xa84300, 0xe74c3c, 0xad1457, 0x11806a]

class Emby:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/emby.json')

    if 'address' not in self.conf or not self.conf['address']:
      self.conf['address'] = input('Enter emby url: ')
      self.conf.save()
    if 'watching' not in self.conf:
      self.conf['watching'] = {'last':None}
      self.conf.save()
    if 'auth' not in self.conf or not self.conf['auth']:
      self.conf['auth'] = {}
      self.conf['auth']['api_key']   = input('Enter emby api key: ')
      self.conf['auth']['userid']    = input('Enter emby user id: ')
      self.conf['auth']['device_id'] = input('Enter emby device id: ')
      self.conf.save()

    self.conn = EmbyPy(self.conf['address'], **self.conf['auth'], ws=True)
    self.conn.connector.set_on_message(self.on_socket_message)
    self.player = Player(bot)
    self.loop.create_task(self.poll())

  async def poll(self):
    latest = await loop.run_in_executor(None, self.conn.latest)
    for l in latest:
      if self.conf['watching']['last'] == l.id:
        break
      item  = await loop.run_in_executor(None, l.update)
      try:
        chans = self.conf['watching'].get(item.parent_id, [])
        for chan_id in chans:
          self.bot.get_channel(chan_id)
          em   = await makeEmbed(item)
          await self.bot.send_message(chan, embed=em)
      except:
        pass
    self.conf['watching']['last'] = latest[0].id
    await asyncio.sleep(30)
    self.loop.create_task(self.poll())

  @commands.group(pass_context=True)
  async def emby(self, ctx):
    """Manage emby stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))

  @emby.command(name='lookup', aliases=['info', 'i'], pass_context=True)
  async def _info(self, ctx, *, item_ids = ''):
    """print emby server info, or an embed for each item id"""
    loop = asyncio.get_event_loop()
    for item_id in item_ids.split():
      item = await loop.run_in_executor(None, self.conn.info, item_id)
      em   = await makeEmbed(item)
      await self.bot.send_message(ctx.message.channel, embed=em)
    if not item_ids:
      info = await loop.run_in_executor(None, self.conn.info)
      await self.bot.say(info)

  @emby.command(name='watch', pass_context=True)
  async def _watch(self, ctx, *, item_ids = ''):
    for item_id in item_ids.split()
      watching = self.conf['watching'].get(item_id)
      if watching and ctx.message.channel.id not in watching:
        self.conf['watching'].get(item_id).append(ctx.message.channel.id)
      elif not watching:
        self.conf['watching'][item_id] = [ctx.message.channel.id]
    self.conf.save()

@emby.command(name='unwatch', pass_context=True)
async def _watch(self, ctx, *, item_ids = ''):
  for item_id in item_ids.split()
    watching = self.conf['watching'].get(item_id)
    if watching and ctx.message.channel.id in watching:
      self.conf['watching'].get(item_id).remove(ctx.message.channel.id)
  self.conf.save()

  @emby.command(name='search', aliases=['find', 's'], pass_context=True)
  async def _search(self, ctx, *, query : str):
    """searches for query on emby, displays first result

    if first "word" in query is a number, returns that many results
    (ignoring the number)
    """

    match = re.search(r'^(\d)+\s+(\S.*)$', query)
    if not query:
      await self.bot.say(formatter.error('missing query'))
      return
    elif match:
      num   = int(match.group(1))
      query = match.group(2)
    else:
      num   = 1

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, self.conn.search, query)
    results = [i for i in results if issubclass(type(i), EmbyObject)]
    if not results:
      await self.bot.say('No results found')
      return

    types_map = {'BoxSet':0, 'Series':1, 'Movie':2, 'Audio':3, 'Person':4}
    m_size    = len(types_map)
    results   = sorted(results, key = lambda x : types_map.get(x.type, m_size))

    for result in results[:num]:
      await loop.run_in_executor(None, result.update)
      em = await makeEmbed(result)
      await self.bot.send_message(ctx.message.channel, embed=em)

  @emby.command(pass_context=True)
  async def join(self, ctx, *, channel : discord.Channel):
    await self.player(ctx, channel)

  @emby.command(pass_context=True)
  async def summon(self, ctx):
    await self.summon(ctx)

  @emby.command(pass_context=True)
  async def play(self, ctx, *, song : str):
    await self.player.play(ctx, song)

  @emby.command(pass_context=True)
  async def volume(self, server, value : int):
    await self.player.volume(server, value)

  @emby.command(pass_context=True)
  async def pause(self, ctx):
    await self.pause.play(ctx)

  @emby.command(pass_context=True)
  async def resume(self, ctx):
    await self.resume.play(ctx)

  @emby.command(pass_context=True)
  async def stop(self, ctx):
    await self.player.stop(ctx)

  @emby.command(pass_context=True)
  async def skip(self, ctx):
    await self.skip.stop(ctx)

  @emby.command(pass_context=True)
  async def playing(self, ctx):
    await self.playing.stop(ctx)

  async def on_socket_message(self, message):
    if message['MessageType'] == 'LibraryChanged':
      for eid in message['ItemsAdded']:
        logging.info(eid+' has been added to emby')
        print(eid+' has been added to emby')

  def __unload(self):
    self.player.unload()

async def makeEmbed(item):
  loop = asyncio.get_event_loop()
  em = Embed()
  img_url          = item.primary_image_url
  if 'https' in img_url:
    img_url        = await loop.run_in_executor(None, puush.get_url, img_url)
  em.title         = item.name
  try:
    em.description = item.overview
  except:
    em.description = item.media_type
  em.url           = item.url
  em.colour        = getColour(item.id)
  em.set_thumbnail(url=img_url)
  return em

def getColour(string : str):
  str_hash = hashlib.md5()
  str_hash.update(string.strip().encode())
  str_hash = int(str_hash.hexdigest(), 16)
  return colours[str_hash % len(colours)]

def setup(bot):
  bot.add_cog(Emby(bot))
