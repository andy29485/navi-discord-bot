#!/usr/bin/env python3

from discord.ext import commands
from .utils.config import Config
from .utils.format import *
from discord import Embed
import asyncio
import hashlib
from embypy import Emby as EmbyPy
from embypy.objects import EmbyObject
import re

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
    if 'auth' not in self.conf or not self.conf['auth']:
      self.conf['auth'] = {}
      self.conf['auth']['api_key']   = input('Enter emby api key: ')
      self.conf['auth']['userid']    = input('Enter emby user id: ')
      self.conf['auth']['device_id'] = input('Enter emby device id: ')
      self.conf.save()

    self.conn = EmbyPy(self.conf['address'], **self.conf['auth'], ws=True)
    self.conn.connector.set_on_message(self.on_socket_message)

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
      em   = await loop.run_in_executor(None, makeEmbed, item)
      await self.bot.send_message(ctx.message.channel, embed=em)
    if not item_ids:
      info = await loop.run_in_executor(None, self.conn.info)
      await self.bot.say(info)

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
      em = await loop.run_in_executor(None, makeEmbed, result)
      await self.bot.send_message(ctx.message.channel, embed=em)

  def on_socket_message(self, message):
    if message['MessageType'] == 'LibraryChanged':
      for eid in message['ItemsAdded']:
        print(eid+'has been added')

def makeEmbed(item):
  em = Embed()
  em.title       = item.name
  em.description = item.overview
  em.url         = item.url
  em.colour      = getColour(item.id)
  em.set_thumbnail(url=item.primary_image_url)
  return em

def getColour(string : str):
  str_hash = hashlib.md5()
  str_hash.update(string.strip().encode())
  str_hash = int(str_hash.hexdigest(), 16)
  return colours[str_hash % len(colours)]

def setup(bot):
  bot.add_cog(Emby(bot))
