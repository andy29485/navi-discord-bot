#!/usr/bin/env python3

if __name__ == '__main__' and __package__ is None:
  from os import sys, path, makedirs
  sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import discord
from discord.ext import commands
from discord.abc import GuildChannel as GC
import asyncio
import aiohttp
import datetime
import re, sys, os
import traceback

from cogs import *
from includes.utils.config import Config
import includes.utils.format as formatter

if not os.path.exists('configs'):
  makedirs('configs')
if not os.path.exists('logs'):
  makedirs('logs')

auth = Config('configs/auth.json')

import logging
from logging.handlers import TimedRotatingFileHandler
current_path = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('navi')
logger.setLevel(logging.INFO)
logformat = logging.Formatter(
  '%(asctime)s:%(name)s:%(levelname)s' + \
  '(%(pathname)s:%(lineno)s) - %(message)s'
)

#to log errors
path = os.path.join(current_path, 'logs/error.log')
error_log = logging.FileHandler(path)
error_log.setLevel(logging.ERROR)
error_log.setFormatter(logformat)

#to log debug messages
path = os.path.join(current_path, 'logs/navi')
fh = TimedRotatingFileHandler(path, when='midnight')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logformat)
fh.suffix = '%Y-%m-%d.log'

# finalize logger setup
logger.addHandler(error_log)
logger.addHandler(fh)

# discordpy logging
dlog = logging.getLogger('discord')
dlog.setLevel(logging.WARNING)
dlog_h = logging.FileHandler(
  filename='logs/discord.log',
  encoding='utf-8',
  mode='w'
)
dlog_h.setFormatter(logformat)
dlog.addHandler(dlog_h)

# asyncio logging
alog = logging.getLogger('asyncio')
alog.setLevel(logging.WARNING)
alog_h = logging.FileHandler(
  filename='logs/asyncio.log',
  encoding='utf-8',
  mode='w'
)
alog_h.setFormatter(logformat)
alog.addHandler(alog_h)

# setup bot information
prefix = ['.']
description = "Andy29485's bot"
help_attrs  = {'hidden': True}

bot = commands.Bot(command_prefix=prefix, description=description,
                   pm_help=None,          help_attrs=help_attrs
)

@bot.event
async def on_ready():
  # attempt to load up cogs
  for cog in auth.get('cogs', []):
    try:
      bot.load_extension(cog)
    except Exception as e:
      print('Error loading {}\n{}: {}'.format(cog, type(e).__name__, e))

  logger.info(
    'bot started %s#%s (<@%d>)',
    bot.user.name, bot.user.discriminator, bot.user.id
  )
  # print "debug" info to the command line
  print('Logged in as:')
  print('Username: ' + bot.user.name + '#' +bot.user.discriminator)
  print(f'ID: {bot.user.id}')
  print('------')

  # set time started
  if not hasattr(bot, 'uptime'):
    bot.uptime = datetime.datetime.utcnow()

  # Set help command dialogue
  await bot.change_presence(activity=discord.Game(f'{prefix[0]}help'))

@bot.event
async def on_error(ctx, error):
  e_tb  = traceback.format_exception(
    error.__class__, error, error.__traceback__
  )
  lines = []
  for line in e_tb:
    lines.extend(line.rstrip('\n').splitlines())
  logger.error(f'Unknown error: %s','\n'.join(lines))

@bot.event
async def on_command_error(ctx, error):
  msg = ctx.message
  if isinstance(error, commands.NoPrivateMessage):
    await msg.author.send(formatter.error(
        'This command cannot be used in private messages.'
    ))
  elif isinstance(error, commands.DisabledCommand):
    await msg.channel.send(formatter.error(
        'Sorry. This command is disabled and cannot be used.'
    ))
  elif isinstance(error, commands.CommandInvokeError):
    await msg.channel.send(formatter.error(
        'Command error: {}'.format(error)
    ))
  elif isinstance(error, commands.errors.CheckFailure):
    await msg.channel.send(formatter.error(
      'Sorry you have insufficient permissions to run that command.'
    ))
  else:
    await msg.channel.send(formatter.error(str(error)))

  e_tb  = traceback.format_exception(
    error.__class__, error, error.__traceback__
  )
  lines = []
  for line in e_tb:
    lines.extend(line.rstrip('\n').splitlines())
  logger.error(f'<{msg.author.name}> {msg.content}: %s','\n'.join(lines))

@bot.event
async def on_resumed():
  logger.info('resuming')
  print('resuming...')

@bot.event
async def on_command(ctx):
  msg = ctx.message
  chan = msg.channel
  if (not isinstance(chan, GC)):
    chan = 'PM'
  else:
    chan = '#{0.channel.name} ({0.guild.name})'.format(msg)

  logger.info('{0.author.name} in {1}: {0.content}'.format(msg, chan))

@bot.event
async def on_message(message):
  logger.debug('global on message start')

  if message.author.bot:
    logger.debug('  ignoring message (reason: bot)')
    return

  # check if user is not the ignore list
  perms = Config('configs/perms.json')
  if str(message.author.id) in perms.get('ignore', []):
    logger.debug('  ignoring message (reason: user in ingore list)')
    return


  # check if command is a valid one
  if not re.search('^[\\.!\\?\\$]{2,}', message.content):
    await bot.process_commands(message)
  logger.debug('global on message end')

# load token and start bot
#   if not token, ask
while len(auth.get('token', '')) < 30:
  auth['token'] = input("Please enter bot's token: ")
  auth.save()

if len(auth.get('cogs', [])) == 0:
  is_cog = lambda fname: ord(fname[0]) <= ord('z') \
                     and ord(fname[0]) >= ord('a') \
                     and fname.endswith('.py')
  auth['cogs'] = ['cogs.'+x[:-3] for x in os.listdir('cogs/') if is_cog(x)]

#start bot
bot.run(auth['token'])
