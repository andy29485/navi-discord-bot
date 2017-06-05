#!/usr/bin/env python3

if __name__ == '__main__' and __package__ is None:
  from os import sys, path, makedirs
  sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import discord
from discord.ext import commands
import asyncio
import aiohttp
import datetime
import re, sys, os
from cogs import *
from cogs.utils.config import Config
import cogs.utils.format as formatter

starting_cogs = [
  'cogs.general',
  'cogs.az',
  'cogs.admin',
  'cogs.internet',
  'cogs.quotes',
  'cogs.server',
  'cogs.regex',
  'cogs.groupme',
  'cogs.dnd',
  'cogs.emby',
  'cogs.nsfw'
]


if not path.exists('configs'):
  makedirs('configs')
if not path.exists('logs'):
  makedirs('logs')

import logging
from logging.handlers import TimedRotatingFileHandler
current_path = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('navi')
logger.setLevel(logging.DEBUG)

#to log debug messages
debug_log = logging.FileHandler(os.path.join(current_path, 'logs/navi.log'))
debug_log.setLevel(logging.DEBUG)

#to log errors
errror_log = logging.FileHandler(os.path.join(current_path, 'logs/error.log'))
errror_log.setLevel(logging.ERROR)

fh = TimedRotatingFileHandler(os.path.join(current_path, 'logs/navi'),
                              when='midnight'
)
fh.suffix = '%Y-%m-%d.log'

logger.addHandler(debug_log)
logger.addHandler(errror_log)
logger.addHandler(fh)

prefix = ['.']
description = 'Andy29485\'s bot'
help_attrs = dict(hidden=True)

bot = commands.Bot(command_prefix=prefix, description=description,
                   pm_help=None, help_attrs=help_attrs)

@bot.async_event
async def on_ready():
  for cog in starting_cogs:
    try:
      bot.load_extension(cog)
    except Exception as e:
      print('Failed to load cog {}\n{}: {}'.format(cog, type(e).__name__, e))
  print('Logged in as:')
  print('Username: ' + bot.user.name + '#' +bot.user.discriminator)
  print('ID: ' + bot.user.id)
  print('------')
  if not hasattr(bot, 'uptime'):
    bot.uptime = datetime.datetime.utcnow()
  await bot.change_presence(game=discord.Game(name='{}help'.format(prefix[0])))

@bot.async_event
async def on_command_error(error, ctx):
  if isinstance(error, commands.NoPrivateMessage):
    await bot.send_message(ctx.message.author, formatter.error(
                            'This command cannot be used in private messages.'))
  elif isinstance(error, commands.DisabledCommand):
    await bot.send_message(ctx.message.channel, formatter.error(
                         'Sorry. This command is disabled and cannot be used.'))
  elif isinstance(error, commands.CommandInvokeError):
    logger.error('In {0.command.qualified_name}:'.format(ctx))
    logger.error(error.original.__traceback__)
    logger.error('{0.__class__.__name__}: {0}'.format(error.original))
    await bot.send_message(ctx.message.channel,formatter.error(
        'Command error: {}'.format(error))
    )
  elif isinstance(error, commands.errors.CheckFailure):
    await bot.send_message(ctx.message.channel, formatter.error(
                'Sorry you have insufficient permissions to run that command.'))
  else:
    await bot.send_message(ctx.message.channel, formatter.error(str(error)))

@bot.async_event
async def on_resumed():
  print('resuming...')

@bot.async_event
async def on_command(command, ctx):
  msg = ctx.message
  chan = None
  if ctx.message.channel.is_private:
    chan = 'PM'
  else:
    chan = '#{0.channel.name} ({0.server.name})'.format(msg)

  logger.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(
            msg, chan)
  )

@bot.async_event
async def on_message(message):
  if message.author.bot:
    return

  if not re.search('^[\\.!\\?\\$]{2,}', message.content):
    await bot.process_commands(message)

auth = Config('configs/auth.json')

while 'token' not in auth or len(auth['token']) < 30:
  auth['token'] = input('Please enter bot\'s token: ')

#start bot
bot.run(auth['token'])
