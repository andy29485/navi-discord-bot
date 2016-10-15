#!/usr/bin/env python3

import random
import re
import time
import asyncio
from urllib import parse as urlencode
from discord.ext import commands
from .utils import format as formatter
from .utils import perms
from .utils.config import Config

class General:
  def __init__(self, bot):
    self.bot = bot
    self.stopwatches = {}
    self.conf = Config('configs/general.json')
    self.poll_sessions = []

  @commands.command(hidden=True)
  async def ping(self):
    """Pong."""
    await self.bot.say("Pong.")

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
  
  @commands.command(name="8", aliases=["8ball"])
  async def _8ball(self, *, question : str):
    """Ask 8 ball a question
    Question must end with a question mark.
    """
    if question.endswith("?") and question != "?":
      await self.bot.say("`" + random.choice(self.config['8-ball']) + "`")
    else:
      await self.bot.say("That doesn't look like a question.")

  @commands.command(aliases=["sw"], pass_context=True)
  async def stopwatch(self, ctx):
    """Starts/stops stopwatch"""
    author = ctx.message.author
    if not author.id in self.stopwatches:
      self.stopwatches[author.id] = int(time.perf_counter())
      await self.bot.say(author.mention + " Stopwatch started!")
    else:
      tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
      tmp = str(datetime.timedelta(seconds=tmp))
      await self.bot.say("{} Stopwatch stopped! Time: **{}**".format(
                         author.mention, tmp))
      self.stopwatches.pop(author.id, None)
      
  @commands.command()
  async def lmgtfy(self, *, search_terms : str):
    """Creates a lmgtfy link"""
    search_terms = urlencode('q': search_terms)
    await self.bot.say("http://lmgtfy.com/?{}".format(search_terms))

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
