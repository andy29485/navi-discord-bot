#!/usr/bin/env python3

import re
import time
import random
import logging
import asyncio
from discord.ext import commands
from datetime import datetime, timedelta
from includes.utils.poll import Poll
from includes.utils.config import Config
from includes.utils.format import *
from includes.utils.reminders import Reminder

logger = logging.getLogger('navi.general')

class General:
  def __init__(self, bot):
    self.bot         = bot
    self.loop        = bot.loop
    self.stopwatches = {}
    self.conf        = Config('configs/general.json')

    heap = self.bot.get_cog('HeapCog')

    if 'responses' not in self.conf:
      self.conf['responses'] = {}
    if 'todo' not in self.conf:
      self.conf['todo'] = {}
    if 'situations' not in self.conf:
      self.conf['situations'] = []
    if '8-ball' not in self.conf:
      self.conf['8-ball'] = []
    for rem in self.conf.pop('reminders', []):
      heap.push(rem)
    self.conf.save()


  @commands.command(hidden=True)
  async def ping(self):
    """Pong."""
    await self.bot.say("Pong.")

  @commands.command(pass_context=True)
  async def time(self, ctx, first=''):
    '''remind people to hurry up'''
    say = lambda msg: self.bot.send_message(ctx.message.channel, msg)
    if random.randrange(50) or not first.startswith('@'):
      now = datetime.now().replace(microsecond=0)
      await say(now.isoformat().replace('T', ' '))
    else:
      await self.bot.send_typing(ctx.message.channel)
      await asyncio.sleep(1.2)
      await say('ゲネラルリベラル')
      await asyncio.sleep(0.4)
      await say('デフレイスパイラル')
      await asyncio.sleep(0.5)
      await say('ナチュラルミネラル')
      await asyncio.sleep(0.2)
      await say('さあお出で' + (': '+first if first else ''))

  @commands.command(pass_context=True)
  async def invite(self, ctx):
    '''reply with a link that allows this bot to be invited'''
    await self.bot.send_message(
      ctx.message.channel,
      f'https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}'+
      '&permissions=305260592&scope=bot'
    )

  async def tally(self, message):
    chan = message.channel
    user = message.author
    mess = message.content
    loop = asyncio.get_event_loop()

    #bots don't get a vote
    if user.bot:
      return

    if len(mess.strip()) < 2 or \
        mess.strip()[0] in self.bot.command_prefix + ['$','?','!']:
      return

    test_poll = Poll('', [], chan, 0, 1)

    heap = self.bot.get_cog('HeapCog')
    for poll in heap:
      if test_poll == poll:
        await loop.run_in_executor(None, poll.vote, user, mess)

  async def respond(self, message):
    if message.author.bot:
      return

    if len(message.content.strip()) < 2 or \
        message.content.strip()[0] in self.bot.command_prefix + ['$','?','!']:
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
        for j in re.findall("\\(.*\\|.*\\)", rep):
          rep = rep.replace(j, random.choice(j[1:-1].split("|")))
        msg = re.sub("(?i){}".format(i[0]), rep, message.content)
        if rep:
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

    total,roll = await loop.run_in_executor(None, self.rolls, dice)
    roll = '\n'.join(roll)
    message = ctx.message.author.mention + ':\n'
    if '\n' in roll:
      message += code(roll + f'\nTotal: {total}')
    else:
      message += inline(roll)
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

  @commands.group(aliases=['t', 'td'], pass_context=True)
  async def todo(self, ctx):
    '''
    manages user TODO list
    Note: if no sub-command is specified, TODOs will be listed
    '''
    if ctx.invoked_subcommand is None:
      await self._td_list(ctx)

  @todo.command(name='list', aliases=['l', 'ls'], pass_context=True)
  async def _td_list_wp(self, ctx):
    '''
    prints your complete todo list
    '''
    await self._td_list(ctx)

  @todo.command(name='add', aliases=['a', 'insert', 'i'], pass_context=True)
  async def _td_add(self, ctx, *, task : str):
    '''
    adds a new task to your todo list
    '''
    todos = self.conf['todo'].get(ctx.message.author.id, [])
    todos.append([False, task])
    self.conf['todo'][ctx.message.author.id] = todos
    self.conf.save()
    await self.bot.say(ok())

  @todo.command(name='done', aliases=['d', 'complete', 'c'], pass_context=True)
  async def _td_done(self, ctx, *, index : int):
    '''
    sets/unsets a task as complete
    Note: indicies start at 1
    '''
    todos = self.conf['todo'].get(ctx.message.author.id, [])
    if len(todos) < index or index <= 0:
      await self.bot.say(error('Invalid index'))
    else:
      index -= 1
      todos[index][0] = not todos[index][0]
      self.conf['todo'][ctx.message.author.id] = todos
      self.conf.save()
      await self.bot.say(ok())

  @todo.command(name='remove', aliases=['rem', 'rm', 'r'], pass_context=True)
  async def _td_remove(self, ctx, *, index : int):
    '''
    remove a task from your todo list
    Note: indicies start at 1
    '''
    todos = self.conf['todo'].get(ctx.message.author.id, [])
    if len(todos) < index or index <= 0:
      await self.bot.say(error('Invalid index'))
    else:
      task = todos.pop(index - 1)
      self.conf['todo'][ctx.message.author.id] = todos
      self.conf.save()
      await self.bot.say(ok('Removed task #{}'.format(index)))

  async def _td_list(self, ctx):
    todos = self.conf['todo'].get(ctx.message.author.id, [])
    if not todos:
      await self.bot.send_message(ctx.message.channel, 'No TODOs found.')
    else:
      #TODO - ensure that the outgoing message is not too long
      msg     = 'TODO:\n'
      length  = len(str(len(todos)))
      done    = '{{:0{}}} - ~~{{}}~~\n'.format(length)
      working = '{{:0{}}} - {{}}\n'.format(length)
      for i, todo in enumerate(todos, 1):
        if todo[0]:
          msg += done.format(i, todo[1])
        else:
          msg += working.format(i, todo[1])
      await self.bot.send_message(ctx.message.channel, msg)

  @commands.group(aliases=["sw"], pass_context=True)
  async def stopwatch(self, ctx):
    """
    manages user stopwatch
    starts/stops/unpauses (depending on context)
    """
    if ctx.invoked_subcommand is None:
      aid = ctx.message.author.id
      if aid in self.stopwatches and self.stopwatches[aid][0]:
        await self._sw_stop(ctx)
      else:
        await self._sw_start(ctx)

  @stopwatch.command(name='start',
                     aliases=['unpause','u','resume','r'],
                     pass_context=True)
  async def _sw_start_wrap(self, ctx):
    """
    unpauses or creates new stopwatch
    """
    await self._sw_start(ctx)

  async def _sw_start(self, ctx):
    aid = ctx.message.author.id
    tme = ctx.message.timestamp.timestamp()
    if aid in self.stopwatches and self.stopwatches[aid][0]:
      await self.bot.send_message(ctx.message.channel,
                                  'You\'ve already started a stopwatch.'
      )
    elif aid in self.stopwatches:
      self.stopwatches[aid][0] = tme
      await self.bot.send_message(ctx.message.channel, 'Stopwatch resumed.')
    else:
      self.stopwatches[aid] = [tme, 0]
      await self.bot.send_message(ctx.message.channel, 'Stopwatch started.')

  @stopwatch.command(name='stop', aliases=['end','e'], pass_context=True)
  async def _sw_stop_wrap(self, ctx):
    """
    prints time and deletes timer

    works even if paused
    """
    await self._sw_stop(ctx)

  async def _sw_stop(self, ctx):
    aid = ctx.message.author.id
    now = ctx.message.timestamp.timestamp()
    old = self.stopwatches.pop(aid, None)
    if old:
      if old[0]:
        tme = now - old[0] + old[1]
      else:
        tme = old[1]
      tme = str(timedelta(seconds=tme))
      msg = '```Stopwatch stopped: {}\n'.format(tme)
      for lap in zip(range(1,len(old)), old[2:]):
        msg += '\nLap {0:03} - {1}'.format(*lap)
      msg += '```'
      await self.bot.send_message(ctx.message.channel, msg)
    else:
      await self.bot.send_message(ctx.message.channel,
                                  'No stop watches started, cannot stop.'
      )

  @stopwatch.command(name='status', aliases=['look','peak'], pass_context=True)
  async def _sw_status(self, ctx):
    aid = ctx.message.author.id
    now = ctx.message.timestamp.timestamp()
    if aid in self.stopwatches:
      old = self.stopwatches[aid]
      if old[0]:
        tme = now - old[0] + old[1]
      else:
        tme = old[1]
      tme = str(timedelta(seconds=tme))
      msg = '```Stopwatch time: {}'.format(tme)
      if old[0]:
        msg += '\n'
      else:
        msg += ' [paused]\n'
      for lap in zip(range(1,len(old)), old[2:]):
        msg += '\nLap {0:03} - {1}'.format(*lap)
      msg += '```'
      await self.bot.send_message(ctx.message.channel, msg)
    else:
      await self.bot.send_message(ctx.message.channel,
                                  'No stop watches started, cannot look.'
      )

  @stopwatch.command(name='lap', aliases=['l'], pass_context=True)
  async def _sw_lap(self, ctx):
    """
    prints time

    does not pause, does not resume, does not delete
    """
    aid = ctx.message.author.id
    now = ctx.message.timestamp.timestamp()
    if aid in self.stopwatches:
      old = self.stopwatches[aid]
      if old[0]:
        tme = now - old[0] + old[1]
      else:
        tme = old[1]
      tme   = str(timedelta(seconds=tme))
      await self.bot.say("Lap #{:03} time: **{}**".format(len(old)-1, tme))
      if self.stopwatches[aid][-1] != tme:
        self.stopwatches[aid].append(tme)
    else:
      await self.bot.say('No stop watches started, cannot lap.')

  @stopwatch.command(name='pause', aliases=['p','hold','h'], pass_context=True)
  async def _sw_pause(self, ctx):
    """
    pauses the stopwatch

    Also prints current time, does not delete
    """
    aid = ctx.message.author.id
    now = ctx.message.timestamp.timestamp()
    if aid in self.stopwatches and self.stopwatches[aid][0]:
      old = now - self.stopwatches[aid][0] + self.stopwatches[aid][1]
      self.stopwatches[aid] = [0, old]
      old = str(timedelta(seconds=old))
      await self.bot.say("Stopwatch paused: **{}**".format(old))
    elif aid in self.stopwatches:
      await self.bot.say('Stop watch already paused.')
    else:
      await self.bot.say('No stop watches started, cannot pause.')

  def rolls(self, dice):
    out = []

    if not dice:
      dice = ['20']

    gobal_total = 0
    for roll in dice:
      match = re.search('^((\\d+)?d)?(\\d+)([+-]\\d+)?$', roll, re.I)
      message = ''
      total = 0
      if not match:
        message = 'Invalid roll'
      else:
        times = 1
        sides = int(match.group(3))
        add   = 0
        if match.group(2):
          times = int(match.group(2))
        if match.group(4):
          add = int(match.group(4))

        if times > 100:
          message = 'Cannot roll that many dice'
        elif sides > 120:
          message = 'Cannot find a dice with that many sides'
        elif times < 1:
          message = 'How?'
        elif sides < 2:
          message = 'No'
        else:
          for i in range(times):
            num      = random.randint(1, sides)+add
            total   += num
            message += '{}, '.format(num)
          message = message[:-2]
          gobal_total += total
          if times > 1:
            message += ' (sum = {})'.format(total)
      out.append('{}: {}'.format(roll, message))
    return (gobal_total, out)

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
    message += inline(choice)
    await self.bot.say(message)

  @commands.command(name='remindme', pass_context=True, aliases=['remind'])
  async def _add_reminder(self, ctx, *, message : str):
    '''
    adds a reminder

    'at' can be used when specifing exact time
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
    .remind [me] remove <id>
    .remind [me] end <id>
    '''
    heap    = self.bot.get_cog('HeapCog')
    author  = ctx.message.author.id
    channel = ctx.message.channel.id
    match   = re.match(r'(?i)^(me\s+)?(remove|end|stop)\s+(\d+)', message)

    if match:
      rid = int(match.group(3))
      for index,item in enumerate(heap):
        if type(item) == Reminder \
            and item.reminder_id == rid \
            and item.user_id == author:
          heap.pop(index)
          await self.bot.say(ok(f'Message with id {rid} has been removed'))
          return
      else:
        await self.bot.say(ok(f'Could not find message with id {rid}'))
    else:
      r = Reminder(channel, author, message)
      heap.push(r)
      await r.begin(self.bot)

  @commands.command(pass_context=True, aliases=['a', 'ask'])
  async def question(self, ctx):
    '''Answers a question with yes/no'''
    message = ctx.message.author.mention + ':\n'
    message += inline(random.choice(['yes', 'no']))
    await self.bot.say(message)

  @commands.command(pass_context=True)
  async def poll(self, ctx, *, question):
    '''
    Starts a poll
    format:
    poll question? opt1, opt2, opt3 or opt4...
    poll stop|end
    '''
    heap = self.bot.get_cog('HeapCog')

    if question.lower().strip() in ['end', 'stop']:
      for index,poll in enumerate(heap):
        if isinstance(poll, Poll) and poll.channel_id == ctx.message.channel.id:
          heap.pop(index)
          await poll.end(self.bot)
          break
      else:
        await self.bot.say('There is no poll active in this channel')
      return

    match = re.search(r'^(.*?\?)\s*(.*?)$', question)
    if not match:
      await self.bot.say('Question could not be found.')
      return

    options  = split(match.group(2))
    question = escape_mentions(match.group(1))

    poll = Poll(question, options, ctx.message.channel, 600)

    for item in heap:
      if poll == item:
        await self.bot.say('There is a poll active in this channel already')
        return
    heap.push(poll)
    await poll.begin(self.bot)

def split(choices):
  choices = re.split(r'(?i)\s*(?:,|\bor\b)\s*', choices)
  return list(filter(None, choices))

def setup(bot):
  g = General(bot)
  bot.add_listener(g.tally, "on_message")
  bot.add_listener(g.respond, "on_message")
  bot.add_cog(g)
