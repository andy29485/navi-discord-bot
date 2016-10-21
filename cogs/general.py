#!/usr/bin/env python3

import random
import re
import time
import asyncio
from urllib import parse as urlencode
from discord.ext import commands
from .utils import format as formatter
from .utils import perms
from .utils.poll import Poll
from .utils.config import Config

class General:
  def __init__(self, bot):
    self.bot           = bot
    self.stopwatches   = {}
    self.polls         = {}
    self.conf          = Config('configs/general.json')
    self.poll_sessions = []

  @commands.command(hidden=True)
  async def ping(self):
    """Pong."""
    await self.bot.say("Pong.")

  async def respond(self, message):
    for i in self.conf['responses']:
      if re.search("(?i){}".format(i[0]), message.content):
        await bot.send_message(message.channel, re.sub("(?i){}".format(i[0]),
                                                       i[1], message.content))
        return

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
    search_terms = urlencode.urlencode({'q':search_terms})
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
    choices = split(choices)
    message = ctx.message.author.mention + ':\n'
    message += formatter.inline(random.choice(choices))
    await self.bot.say(message)

  @commands.command(pass_context=True, aliases=['a', 'ask'])
  async def question(self, ctx):
    """Answers a question"""
    message = ctx.message.author.mention + ':\n'
    message += formatter.inline(random.choice(['yes', 'no']))
    await self.bot.say(message)

  async def tally(self, message):
    chan = message.channel
    user = message.author
    mess = message.content

    #bots don't get a vote
    if user.bot:
      return

    if len(mess.strip()) < 2 or \
       mess.strip()[0] in self.bot.command_prefix + ['$','?']:
      return

    if chan in self.polls:
      self.polls[chan].vote(user, mess)

  @commands.command(pass_context=True)
  async def poll(self, ctx, *, question):
    """Starts a poll
    format:
    poll question? opt1, opt2, opt3 or opt4...
    poll stop|end
    """

    if question.lower().strip() in ['end', 'stop']:
      if ctx.message.channel in self.polls:
        await self.polls[ctx.message.channel].stop()
      else:
        await self.bot.say('There is no poll active in this channel')
      return

    if ctx.message.channel in self.polls:
      await self.bot.say('There\'s already an active poll in this channel')
      return

    match = re.search(r'^(.*?\?)\s*(.*?)$', question)
    if not match:
      await self.bot.say('Question could not be found.')
      return

    options  = split(match.group(2))
    question = formatter.escape_mentions(match.group(1))

    poll = Poll(self.bot, ctx.message.channel, question, options,
                self.conf['polls']['duration'], self.polls)

    self.polls[ctx.message.channel] = poll
    await poll.start()


def split(choices):
  choices = re.split(r'(?i)\s*(?:,|\bor\b)\s*', choices)
  return list(filter(None, choices))

def setup(bot):
  g = General(bot)
  bot.add_listener(g.tally, "on_message")
  bot.add_listener(g.respond, "on_message")
  bot.add_cog(g)

