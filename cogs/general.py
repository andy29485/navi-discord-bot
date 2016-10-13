#!/usr/bin/env python3

import random
import re
import asyncio
import discord
from discord.ext import commands
import .utils.format as formatter
import .utils.perms as perms

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
  
  @bot.group(pass_context=True)
  async def rep(self, ctx):
    """Manage replacements
    Uses a regex to replace text from users
    """
    if ctx.invoked_subcommand is None:
      await bot.say(formatter.error(
             'Error, {0.subcommand_passed} is not a valid command'.format(ctx)
      ))

  @rep.command(name='add', pass_context=True)
  async def _add(self, ctx):
    """adds a new replacement
    Format `s/old/new/`"""
    
    #Find requested replacement
    rep = re.match('s/(.*?[^\\](\\\\)*)/(.*?[^\\](\\\\)*)/g?',
                   ctx.message.content)
    
    #ensure that replace was found before proceeding
    if not rep:
      await bot.say(formatter.error('Could not find valid regex'))
      return
    
    #check regex for validity
    try:
      re.compile(rep.group(1))
    except re.error:
      await bot.say(formatter.error('regex is invalid'))
      return
    
    #check that regex does not already exist
    if rep.group(1) in self.replacements:
      await bot.say(formatter.error('regex already exists'))
      return
    
    self.replacements[rep.group(1)] = [rep.group(3), ctx.message.author.id]
    await bot.say(formatter.ok())
  
  @rep.command(name='edit', pass_context=True)
  async def _edit(self, ctx):
  """adds a new replacement
    Format `s/old/new/`"""
    
    #Find requested replacement
    rep = re.match('s/(.*?[^\\](\\\\)*)/(.*?[^\\](\\\\)*)/g?',
                   ctx.message.content)
    
    #ensure that replace was found before proceeding
    if not rep:
      await bot.say(formatter.error('Could not find valid regex'))
      return
    
    #check regex for validity
    try:
      re.compile(rep.group(1))
    except re.error:
      await bot.say(formatter.error('regex is invalid'))
      return
    
    #ensure that replace was found before proceeding
    if rep.group(1) not in self.replacements:
      await bot.say(formatter.error('Regex not in replacements.'))
      return
    
    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[rep.group(1)][1]
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot edit')
    
    self.replacements[rep.group(1)] = [rep.group(3), ctx.message.author.id]
    await bot.say(formatter.ok())
  
  @rep.command(name='remove', aliases=['rm'], pass_context=True)
  async def _rm(self, ctx):
    """remove an existing replacement"""
    
    #Find requested replacement
    rep = re.match('(s/)?(.*?[^\\](\\\\)*)(/)?',
                   ctx.message.content)
    
    #ensure that replace was found before proceeding
    if not rep:
      await bot.say(formatter.error('Could not find valid regex'))
      return
    
    #ensure that replace was found before proceeding
    if rep.group(2) not in self.replacements:
      await bot.say(formatter.error('Regex not in replacements.'))
      return
    
    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[rep.group(2)][1]
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot edit')
    
    self.replacements.pop(rep.group(2))
    await bot.say(formatter.ok())
  
  @rep.command(name='list', aliases=['ls'])
  async def _ls(self):
    """list existing replacements"""
    msg = ''
    
    for rep in self.replacements:
      msg = 's/{}/{}/\n'.format(rep, self.replacements[rep][0])
    msg = msg[:-1]
    
    await bot.say(formatter.code(msg))

def setup(bot):
  bot.add_cog(General(bot))
