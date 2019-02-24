#!/usr/bin/env python3

import asyncio
import logging
import random
from datetime import datetime
from discord.ext import commands
from includes.utils import format as formatter
from includes.utils import perms
from includes.utils.config import Config

logger = logging.getLogger('navi.quotes')

class Quote(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.quotes_dict = Config('configs/quotes.json')
    if 'quotes' not in self.quotes_dict:
      self.quotes_dict['quotes'] = []

  @commands.group(aliases=['q', 'quote'])
  async def quotes(self, ctx):
    """Manage quotes"""

    if ctx.invoked_subcommand is None:
      async with ctx.typing():
        message = ctx.message.content
        try:
          index = int(ctx.subcommand_passed)
          if index >= len(self.quotes_dict['quotes']):
            await ctx.send(formatter.error(
                 'Quote {} does not exist'.format(index)
            ))
          else:
            quote = self.quotes_dict['quotes'][index]
            message = 'On {}:\n{}'.format(quote['date'],
                                          formatter.code(quote['quote']))
            await ctx.send(message)
        except:
          await ctx.send(self._random(message))

  @quotes.command(name='add')
  async def _add(self, ctx, *, quote):
    """adds a quote"""
    async with ctx.typing():
      for i in self.quotes_dict['quotes']:
        if quote.lower() == i['quote'].lower():
          await ctx.send(formatter.error('Quote already exists'))
          return

      index = len(self.quotes_dict['quotes'])
      date  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      self.quotes_dict['quotes'].append({
          'id':     str(ctx.message.author.id),
          'date':   date,
          'quote':  quote,
      })
      self.quotes_dict.save()

      await ctx.send(formatter.ok('quote added, index {}'.format(index)))

  @quotes.command()
  async def random(self, ctx):
    message = ' '.join(ctx.message.content.split()[1:])
    await ctx.send(self._random(message))

  def _random(self, message):
    quotes = self.quotes_dict['quotes']

    message = message.split()[1:]

    if message:
      quotes = []
      for quote in self.quotes_dict['quotes']:
        ok = True
        for w in message:
          if w.lower() not in quote['quote'].lower():
            ok = False
            break
        if ok:
          quotes.append(quote)

    if not quotes:
      return formatter.error('No quotes found')
    quote = random.choice(quotes)
    return 'On {}:\n{}'.format(quote['date'], formatter.code(quote['quote']))

  @quotes.command(name='remove', aliases=['rm'])
  async def _rm(self, ctx, index : int):
    """remove an existing replacement by index"""
    async with ctx.typing():
      if index >= len(self.quotes_dict['quotes']):
        await ctx.send(formatter.error(
             'Quote {} does not exist'.format(index)
        ))
        return

      if str(ctx.message.author.id) != self.quotes_dict['quotes'][index]['id'] \
         and not perms.check_permissions(ctx.message, manage_messages=True):
          raise commands.errors.CheckFailure('Cannot delete')

      self.quotes_dict['quotes'].pop(index)
      self.quotes_dict.save()

      await ctx.send(formatter.ok())

def setup(bot):
  bot.add_cog(Quote(bot))
