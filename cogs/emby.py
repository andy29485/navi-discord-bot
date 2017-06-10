#!/usr/bin/env python3

from discord.ext import commands
import cogs.utils.emby_helper as emby_helper
import cogs.utils.format as formatter
import discord
import asyncio
import logging
from embypy.objects import EmbyObject
import re

class Emby:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = emby_helper.conf
    self.conn = emby_helper.conn
    #self.conn.connector.set_on_message(self.on_socket_message)
    self.loop = self.bot.loop
    self.loop.create_task(self.poll())

  async def poll(self):
    while True:
      latest = await self.loop.run_in_executor(None, self.conn.latest)
      for l in latest:
        if self.conf['watching']['last'] == l.id:
          break
        item = t  = await self.loop.run_in_executor(None, l.update)
        while t.parent_id:
          t = await self.loop.run_in_executor(None,self.conn.info,t.parent_id)
          try:
            chans = self.conf['watching'].get(t.id, [])
            for chan_id in chans:
              chan = self.bot.get_channel(chan_id)
              em   = await emby_helper.makeEmbed(item, 'New item added: ')
              await self.bot.send_message(chan, embed=em)
          except:
            break
      self.conf['watching']['last'] = latest[0].id
      self.conf.save()
      await asyncio.sleep(30)

  @commands.group(pass_context=True)
  async def emby(self, ctx):
    """Manage emby stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))

  @emby.command(name='lookup', aliases=['info', 'i'], pass_context=True)
  async def _info(self, ctx, *, item_ids = ''):
    """print emby server info, or an embed for each item id"""
    for item_id in item_ids.split():
      item = await self.loop.run_in_executor(None, self.conn.info, item_id)
      em   = await emby_helper.makeEmbed(item)
      await self.bot.send_message(ctx.message.channel, embed=em)
    if not item_ids:
      info = await self.loop.run_in_executor(None, self.conn.info)
      await self.bot.say(info)

  @emby.command(name='watch', aliases=['w'], pass_context=True)
  async def _watch(self, ctx, *, item_ids = ''):
    """
    Add show id to follow list

    Usage: .emby watch <show id>
    When an episode for that show is added to emby,
    the bot will alert this channel of that
    """
    for item_id in item_ids.split():
      watching = self.conf['watching'].get(item_id)
      if watching and ctx.message.channel.id not in watching:
        self.conf['watching'].get(item_id).append(ctx.message.channel.id)
      elif not watching:
        self.conf['watching'][item_id] = [ctx.message.channel.id]
    await self.bot.say(formatter.ok())
    self.conf.save()

  @emby.command(name='unwatch', aliases=['uwatch', 'uw'], pass_context=True)
  async def _uwatch(self, ctx, *, item_ids = ''):
    """
    Remove show id from this channel;s follow list

    Usage: .emby unwatch <show id>
    see ".emby watch" for more details
    """
    for item_id in item_ids.split():
      watching = self.conf['watching'].get(item_id)
      if watching and ctx.message.channel.id in watching:
        self.conf['watching'].get(item_id).remove(ctx.message.channel.id)
    await self.bot.say(formatter.ok())
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

    results = await self.loop.run_in_executor(None, self.conn.search, query)
    results = [i for i in results if issubclass(type(i), EmbyObject)]
    if not results:
      await self.bot.say('No results found')
      return

    types_map = {'BoxSet':0, 'Series':1, 'Movie':2, 'Audio':3, 'Person':4}
    m_size    = len(types_map)
    results   = sorted(results, key = lambda x : types_map.get(x.type, m_size))

    for result in results[:num]:
      await self.loop.run_in_executor(None, result.update)
      em = await emby_helper.makeEmbed(result)
      await self.bot.send_message(ctx.message.channel, embed=em)

  async def on_socket_message(self, message):
    if message['MessageType'] == 'LibraryChanged':
      for eid in message['ItemsAdded']:
        logging.info(eid+' has been added to emby')
        print(eid+' has been added to emby')

def setup(bot):
  bot.add_cog(Emby(bot))
