#!/usr/bin/env python3

from discord.ext import commands
from .utils.config import Config
from .utils.format import *
from discord import Embed
import asyncio
import hashlib
from embypy import Emby
from embypy.objects import EmbyObject
import re

colours = [0x1f8b4c, 0xc27c0e, 0x3498db, 0x206694, 0x9b59b6,
           0x71368a, 0xe91e63, 0xe67e22, 0xf1c40f, 0x1abc9c,
           0x2ecc71, 0xa84300, 0xe74c3c, 0xad1457, 0x11806a]

class E:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/emby.json')
    self.conn = Emby(self.conf['address'], **self.conf['auth'])

  @commands.group(pass_context=True)
  async def emby(self, ctx):
    """Manage emby stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))

  @emby.command(name='search', aliases=['find', 's'], pass_context=True)
  async def _add(self, ctx, *, query):
    """searches for query on emby, displays first result

    if first "word" in query is a number, returns that many results
    """

    loop = asyncio.get_event_loop()
    num = 1
    match = re.search(query, '^(\\d+)\\s(.*)$')
    if match:
      num   = int(match.group(1))
      num   = num if num < 5 else 5
      num   = num if num > 1 else 1
      query = match.group(2)

    results = await loop.run_in_executor(None, self.conn.search, query)
    results = [i for i in results if issubclass(type(i), EmbyObject)]
    if not results:
      await self.bot.say('No results found')
      return

    types_map = {'Series':0, 'Movie':1, 'Audio':2, 'Person':3}
    m_size    = len(types_map)
    results   = sorted(results, key = lambda x : types_map.get(x.type, m_size))

    for result in results[:num]:
      await loop.run_in_executor(None, result.update)
      em = await loop.run_in_executor(None, makeEmbed, result)
      await self.bot.send_message(ctx.message.channel, embed=em)

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
  bot.add_cog(E(bot))
