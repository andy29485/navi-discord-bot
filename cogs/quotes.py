#!/usr/bin/env python3

import asyncio
import random
from datetime import datetime
from discord.ext import commands
from cogs.utils import format as formatter
from cogs.utils import perms
from cogs.utils.config import Config

class Quote:
  def __init__(self, bot):
    self.bot = bot
    self.quotes_dict = Config('configs/quotes.json')
    if 'quotes' not in self.quotes_dict:
      self.quotes_dict['quotes'] = []

  @commands.group(pass_context=True, aliases=['q', 'quote'])
  async def quotes(self, ctx):
    """Manage quotes"""

    if ctx.invoked_subcommand is None:
      message = ctx.message.content
      try:
        index = int(ctx.subcommand_passed)
        if index >= len(self.quotes_dict['quotes']):
          await self.bot.say(formatter.error(
               'Quote {} does not exist'.format(index)
          ))
        else:
          quote = self.quotes_dict['quotes'][index]
          message = 'On {}:\n{}'.format(quote['date'],
                                        formatter.code(quote['quote']))
          await self.bot.say(message)
      except:
        await self.bot.say(self._random(message))

  @quotes.command(name='add', pass_context=True)
  async def _add(self, ctx, *, quote):
    """adds a quote"""

    for i in self.quotes_dict['quotes']:
      if quote.lower() == i['quote'].lower():
        await self.bot.say(formatter.error('Quote already exists'))
        return

    index = len(self.quotes_dict['quotes'])
    date  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    self.quotes_dict['quotes'].append({'date':date, 'quote':quote,
                                  'id':ctx.message.author.id})
    self.quotes_dict.save()

    await self.bot.say(formatter.ok('quote added, index {}'.format(index)))

  @quotes.command(pass_context=True)
  async def random(self, ctx):
    message = ' '.join(ctx.message.content.split()[1:])
    await self.bot.say(self._random(message))

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

  @quotes.command(name='remove', aliases=['rm'], pass_context=True)
  async def _rm(self, ctx, index : int):
    """remove an existing replacement by index"""

    if index >= len(self.quotes_dict['quotes']):
      await self.bot.say(formatter.error(
           'Quote {} does not exist'.format(index)
      ))
      return

    if ctx.message.author.id != self.quotes_dict['quotes'][index]['id'] \
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot delete')

    self.quotes_dict['quotes'].pop(index)
    self.quotes_dict.save()

    await self.bot.say(formatter.ok())

def setup(bot):
  bot.add_cog(Quote(bot))
