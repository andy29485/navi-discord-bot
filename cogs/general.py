#!/usr/bin/env python3

import random
import re
import asyncio
from discord.ext import commands
from .utils import format as formatter
from .utils import perms
from .utils.config import Config

class General:
  def __init__(self, bot):
    self.bot = bot

  @commands.command(pass_context=True)
  async def roll(self, ctx, *dice):
    'rolls dice given pattern [Nd]S'
    roll = '\n'.join(self.rolls(dice))
    message = ctx.message.author.mention + ':\n'
    if '\n' in roll:
      message += formatter.code(roll)
    else:
      message += formatter.inline(roll)
    await self.bot.say(message)

  def rolls(self, dice):
    out = []

    if not dice:
      dice = [6]

    for roll in dice:
      match = re.search('^((\\d+)?d)?(\\d+)$', roll, re.I)
      message = ''
      if not match:
        message = 'Invalid roll'
      else:
        times = 1
        if match.group(2):
          times = int(match.group(2))
        for i in range(times):
          sides = int(match.group(3))
          message += '{}, '.format(random.randint(1, sides))
        message = message[:-2]
      out.append('{}: {}'.format(roll, message))
    return out

  @commands.command(pass_context=True, aliases=['c', 'choice'])
  async def choose(self, ctx, *, choices):
    """Chooses a value from a comma seperated list"""
    choices = re.split(r'(?i)\s*(?:,|\bor\b)\s*', choices)
    choices = list(filter(None, choices))
    message = ctx.message.author.mention + ':\n'
    message += formatter.inline(random.choice(choices))
    await self.bot.say(message)

  @commands.command(pass_context=True, aliases=['a', 'ask'])
  async def question(self, ctx):
    """Answers a question"""
    message = ctx.message.author.mention + ':\n'
    message += formatter.inline(random.choice(['yes', 'no']))
    await self.bot.say(message)

def setup(bot):
  bot.add_cog(General(bot))
