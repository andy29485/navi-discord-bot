#!/usr/bin/env python3

import random
import re
import time
import asyncio
from urllib import parse as urlencode
from discord.ext import commands
from cogs.utils import format as formatter
from cogs.utils.poll import Poll
from cogs.utils.config import Config
from cogs.utils.reminders import Reminder


class General:
  def __init__(self, bot):
    self.bot           = bot
    self.loop          = bot.loop
    self.stopwatches   = {}
    self.polls         = {}
    self.conf          = Config('configs/general.json')
    self.poll_sessions = []

    if 'reminders' not in self.conf:
      self.conf['reminders'] = []
    if 'responses' not in self.conf:
      self.conf['responses'] = {}
    if 'situations' not in self.conf:
      self.conf['situations'] = []
    if 'polls' not in self.conf:
      self.conf['polls'] = []
    if '8-ball' not in self.conf:
      self.conf['8-ball'] = []
    self.conf.save()

    self.loop.create_task(self.check_reminders())

  @commands.command(hidden=True)
  async def ping(self):
    """Pong."""
    await self.bot.say("Pong.")

  async def tally(self, message):
    chan = message.channel
    user = message.author
    mess = message.content
    loop = asyncio.get_event_loop()

    #bots don't get a vote
    if user.bot:
      return

    if len(mess.strip()) < 2 or \
       mess.strip()[0] in self.bot.command_prefix + ['$','?']:
      return

    if chan in self.polls:
      await loop.run_in_executor(None, self.polls[chan].vote, user, mess)

  async def respond(self, message):
    if message.author.bot:
      return

    if len(message.content.strip()) < 2 or \
       message.content.strip()[0] in self.bot.command_prefix + ['$','?']:
      return

    loop = asyncio.get_event_loop()

    for i in self.conf['responses']:
      if re.search("(?i){}".format(i[0]), message.content):
        rep = i[1]
        subs = {"\\{un\\}"         : message.author.name,
                "\\{um\\}"         : message.author.mention,
                "\\{ui\\}"         : message.author.mention,
                "\\{situations\\}" : random.choice(self.conf['situations'])
               }
        for j in re.findall("\\(.*\\|.*\\)", rep):
          rep = rep.replace(j, random.choice(j[1:-1].split("|")))
        for j in subs:
          rep = await loop.run_in_executor(None, re.sub, j, subs[j], rep)
        msg = re.sub("(?i){}".format(i[0]), rep, message.content)
        if msg:
          await self.bot.send_message(message.channel, msg)
        return

  @commands.command(name='roll', aliases=['r', 'clench'], pass_context=True)
  async def _roll(self, ctx, *dice):
    """rolls dice given pattern [Nd]S[(+|-)C]

    N: number of dice to roll
    S: side on the dice
    C: constant to add or subtract from each die roll
    """
    loop = asyncio.get_event_loop()

    roll = '\n'.join(await loop.run_in_executor(None, self.rolls, dice))
    message = ctx.message.author.mention + ':\n'
    if '\n' in roll:
      message += formatter.code(roll)
    else:
      message += formatter.inline(roll)
    await self.bot.say(message)

  @commands.command(name="8ball", aliases=["8"])
  async def _8ball(self, *, question : str):
    """Ask 8 ball a question

    Question must end with a question mark.
    """
    if question.endswith("?") and question != "?":
      await self.bot.say("`" + random.choice(self.conf['8-ball']) + "`")
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
      dice = ['20']

    for roll in dice:
      match = re.search('^((\\d+)?d)?(\\d+)([+-]\\d+)?$', roll, re.I)
      message = ''
      if not match:
        message = 'Invalid roll'
      else:
        times = 1
        sides = int(match.group(3))
        add   = 0
        if match.group(2):
          times = int(match.group(2))
        if match.group(4):
          add   = int(match.group(4))

        if times > 100:
          message = 'Cannot roll that many dice  '
        elif sides > 120:
          message = 'Cannot find a dice with that many sides  '
        elif times < 1:
          message = 'How?  '
        elif sides < 2:
          message = 'No  '
        else:
          for i in range(times):
            message += '{}, '.format(random.randint(1, sides)+add)
        message = message[:-2]
      out.append('{}: {}'.format(roll, message))
    return out

  @commands.command(pass_context=True, aliases=['c', 'choice'])
  async def choose(self, ctx, *, choices):
    """Chooses a value from a comma seperated list"""
    choices     = split(choices)
    choice      = random.choice(choices)
    choice_reps = {
       r'(?i)^(should)\s+I\s+'                         : r'You \1 ',
       r'(?i)^([wcs]hould|can|are|were|is)\s+(\S+)\s+' : r'\2 \1 ',
       r'\?$'                                          : '.',
       r'(?i)^am\s+I\s+'                               : 'Thou art ',
       r'(?i)\b(I|me)\b'                               : 'you',
       r'(?i)\bmy\b'                                   : 'your'
    }
    for r in choice_reps:
      choice = re.sub(r, choice_reps[r], choice)

    message  = ctx.message.author.mention + ':\n'
    message += formatter.inline(choice)
    await self.bot.say(message)

  @commands.command(name='remindme', pass_context=True, aliases=['remind'])
  async def _add_reminder(self, ctx, *, message : str):
    """
    adds a reminder

    'at' must be used when specifing exact time
    'in' is optional for offsets
    'me' can be seperate or part of the command name (also optinal)
    cannot mix offsets and exact times

    Samples:
    .remind me in 5 h message
    .remind me in 5 hours 3 m message
    .remind me 1 week message
    .remind me 7 months message
    .remindme in 7 months message
    .remind me at 2017-10-23 message
    .remind me at 2017-10-23T05:11:56 message
    .remindme at 2017-10-23 05:11:56 message
    .remindme at 10/23/2017 5:11 PM message
    .remind at 7:11 message
    .remind at 7:11:15 message
"""
    author  = ctx.message.author.mention
    channel = ctx.message.channel.id
    r = Reminder(channel, author, message)
    r.insertInto(self.conf['reminders'])
    self.conf.save()
    await self.bot.say(formatter.ok())

  @commands.command(pass_context=True, aliases=['a', 'ask'])
  async def question(self, ctx):
    """Answers a question with yes/no"""
    message = ctx.message.author.mention + ':\n'
    message += formatter.inline(random.choice(['yes', 'no']))
    await self.bot.say(message)

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

  async def check_reminders(self):
    while True:
      reminders_removed = False
      # if there are valid reminders, process them
      while self.conf['reminders'] and self.conf['reminders'][0].is_ready():
        r = self.conf['reminders'][0].popFrom(self.conf['reminders'])
        c = self.bot.get_channel(r.channel_id)
        await self.bot.send_message(c, r.get_message())
        reminders_removed = True

      if reminders_removed:
        self.conf.save()

      # wait a bit and check again
      await asyncio.sleep(10)


def split(choices):
  choices = re.split(r'(?i)\s*(?:,|\bor\b)\s*', choices)
  return list(filter(None, choices))

def setup(bot):
  g = General(bot)
  bot.add_listener(g.tally, "on_message")
  bot.add_listener(g.respond, "on_message")
  bot.add_cog(g)
