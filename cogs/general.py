#!/usr/bin/env python3

import random
import re
import asyncio
import discord
from discord.ext import commands
from .utils import format as formatter
from .utils import perms
from .utils.config import Config

class General:
  def __init__(self, bot):
    self.bot = bot
    self.replacements = Config('configs/replace.json')

  @commands.command()
  async def roll(self, *dice):
    'rolls dice given pattern [Nd]S'
    message = '\n'.join(self.rolls(dice))
    message = formatter.code(message)
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
  
  @commands.group(pass_context=True)
  async def rep(self, ctx):
    """Manage replacements
    Uses a regex to replace text from users
    """
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error(
             'Error, {0.subcommand_passed} is not a valid command'.format(ctx)
      ))

  @rep.command(name='add', pass_context=True)
  async def _add(self, ctx, *, message):
    """adds a new replacement
    Format `s/old/new/`
    """
    
    #Find requested replacement
    rep = re.match('^s/(.*?[^\\\\](\\\\\\\\)*)/(.*?[^\\\\](\\\\\\\\)*)/g?$',
                   message)
    
    #ensure that replace was found before proceeding
    if not rep:
      await self.bot.say(formatter.error('Could not find valid regex'))
      return
      
    #check regex for validity
    try:
      re.compile(rep.group(1))
      if bad_re(rep.group(1)):
        raise re.error('nothing in pattern')
    except re.error:
      await self.bot.say(formatter.error('regex is invalid'))
      return
    
    #check that regex does not already exist
    if rep.group(1) in self.replacements:
      await self.bot.say(formatter.error('regex already exists'))
      return
    
    self.replacements[rep.group(1)] = [rep.group(3), ctx.message.author.id]
    await self.bot.say(formatter.ok())
  
  @rep.command(name='edit', pass_context=True)
  async def _edit(self, ctx, *, message):
    """edits an existing replacement
    Format `s/old/new/`
    """
    
    #Find requested replacement
    rep = re.match('^s/(.*?[^\\\\](\\\\\\\\)*)/(.*?[^\\\\](\\\\\\\\)*)/g?$',
                   message)
    
    #ensure that replace was found before proceeding
    if not rep:
      await self.bot.say(formatter.error('Could not find valid regex'))
      return
    
    #check regex for validity
    try:
      re.compile(rep.group(1))
      
    except re.error:
      await self.bot.say(formatter.error('regex is invalid'))
      if bad_re(rep.group(1)):
        raise re.error('nothing in pattern')
      return
    
    #ensure that replace was found before proceeding
    if rep.group(1) not in self.replacements:
      await self.bot.say(formatter.error('Regex not in replacements.'))
      return
    
    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[rep.group(1)][1] \
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot edit')
    
    self.replacements[rep.group(1)] = [rep.group(3), ctx.message.author.id]
    await self.bot.say(formatter.ok())
  
  @rep.command(name='remove', aliases=['rm'], pass_context=True)
  async def _rm(self, ctx, *, message):
    """remove an existing replacement"""
    
    #ensure that replace was found before proceeding
    if message not in self.replacements:
      if re.search('^`.*`$', message) and message[1:-1] in self.replacements:
        message = message[1:-1]
      else:
        await self.bot.say(formatter.error('Regex not in replacements.'))
        return
    
    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[message][1] \
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot edit')
    
    self.replacements.pop(message)
    await self.bot.say(formatter.ok())
  
  @rep.command(name='list', aliases=['ls'])
  async def _ls(self):
    """list existing replacements"""
    msg = ''
    
    for rep in self.replacements:
      msg += 's/{}/{}/\n'.format(rep, self.replacements[rep][0])
    msg = msg[:-1]
    
    await self.bot.say(formatter.code(msg))
  
def bad_re(string):
  string_a = re.sub('\\s+', '', string)
  if not string_a:
    return True
  
  string_a = re.sub('\\(\\?[^\\)]\\)', '', string_a)
  if not string_a:
    return True
  
  string_a = re.sub('.\\?', '', string_a)
  if not string_a:
    return True
  
  string_a = re.sub('(?!\\\\)[\\.\\?\\+\\*\\{\\}\\)\\(\\[\\]]', '', string_a)
  if not string_a:
    return True
    
  string_a = re.sub('\\\\[bSDQEs]', '', string_a)
  if not string_a:
    return True
  
  return len(string_a) < 3

def setup(bot):
  bot.add_cog(General(bot))
