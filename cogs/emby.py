#!/usr/bin/env python3

from discord.ext import commands
import includes.utils.emby_helper as emby_helper
import includes.utils.format as formatter
import discord
import asyncio
import logging
from embypy.objects import EmbyObject
import re

logger = logging.getLogger('navi.emby')

class Emby(commands.Cog):
  def __init__(self, bot):
    self.bot  = bot
    self.conf = emby_helper.conf
    self.conn = emby_helper.conn
    #self.conn.connector.set_on_message(self.on_socket_message)
    self.loop = self.bot.loop
    self.loop.create_task(self.poll())

  async def poll(self):
    while self == self.bot.get_cog('Emby'):
      try:
        logger.debug('polling (l = %s)', self.conf['watching']['last'])

        latest = await self.conn.latest(itemTypes='Movie,Video,Episode')
        logger.debug('  got list (size = %d)', len(latest))

        for l in latest:
          logger.debug('  found - %s (%s) [%s]', l.name, l.id, l.parent_id)

          if self.conf['watching']['last'] == l.id:
            logger.debug('    last - breaking')
            break

          item = t = await l.update()
          while t.parent_id:
            t = await t.parent
            logger.debug('    parent: %s', t.id)
            chans = self.conf['watching'].get(t.id, [])
            for chan_id in chans:
              logger.debug('      sending to chan: %s', chan_id)
              chan = self.bot.get_channel(int(chan_id))
              if chan:
                em = await emby_helper.makeEmbed(item, 'New item added: ')
                await chan.send(embed=em)
              else:
                logger.error('        unable to send to channel %s', chan_id)
        self.conf['watching']['last'] = latest[0].id
        self.conf.save()
        await asyncio.sleep(30)
      except:
        logger.exception('Issue with sending latest item(s)')
        break

  @commands.group()
  async def emby(self, ctx):
    """Manage emby stuff"""
    if ctx.invoked_subcommand is None:
      await ctx.send(formatter.error("Please specify valid subcommand"))

  @emby.command(name='lookup', aliases=['info', 'i'])
  async def _info(self, ctx, *, item_ids = ''):
    """print emby server info, or an embed for each item id"""
    async with ctx.typing():
      for item_id in item_ids.split():
        item = await self.conn.info(item_id)
        em   = await emby_helper.makeEmbed(item)
        await ctx.message.channel.send(embed=em)
      if not item_ids:
        info = await self.conn.info()
        await ctx.send(info)

  @emby.command(name='watch', aliases=['w'])
  async def _watch(self, ctx, *, item_ids = ''):
    """
    Add show id to follow list

    Usage: .emby watch <show id>
    When an episode for that show is added to emby,
    the bot will alert this channel of that
    """
    for item_id in item_ids.split():
      watching = self.conf['watching'].get(item_id)
      if watching and str(ctx.message.channel.id) not in watching:
        self.conf['watching'].get(item_id).append(str(ctx.message.channel.id))
      elif not watching:
        self.conf['watching'][item_id] = [str(ctx.message.channel.id)]
    await ctx.send(formatter.ok())
    self.conf.save()

  @emby.command(name='unwatch', aliases=['uwatch', 'uw'])
  async def _uwatch(self, ctx, *, item_ids = ''):
    """
    Remove show id from this channel's follow list

    Usage: .emby unwatch <show id>
    see ".emby watch" for more details
    """
    for item_id in item_ids.split():
      watching = self.conf['watching'].get(item_id)
      if watching and ctx.message.channel.id in watching:
        self.conf['watching'].get(item_id).remove(str(ctx.message.channel.id))
    await ctx.send(formatter.ok())
    self.conf.save()

  @emby.command(name='search', aliases=['find', 's'])
  async def _search(self, ctx, *, query : str):
    """searches for query on emby, displays first result

    if first "word" in query is a number, returns that many results
    (ignoring the number)
    """

    async with ctx.typing():
      match = re.search(r'^(\d)+\s+(\S.*)$', query)
      if not query:
        await ctx.send(formatter.error('missing query'))
        return
      elif match:
        num   = int(match.group(1))
        query = match.group(2)
      else:
        num   = 1

      results = await self.conn.search(query)
      results = [i for i in results if issubclass(type(i), EmbyObject)]
      if not results:
        await ctx.send('No results found')
        return

      for result in results[:num]:
        await result.update()
        em = await emby_helper.makeEmbed(result)
        await ctx.message.channel.send(embed=em)

  async def on_socket_message(self, message):
    if message['MessageType'] == 'LibraryChanged':
      for eid in message['ItemsAdded']:
        logger.info(eid+' has been added to emby')
        print(eid+' has been added to emby')

def setup(bot):
  bot.add_cog(Emby(bot))
