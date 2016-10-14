#!/usr/bin/env python3

import re
import asyncio
from discord.ext import commands
from .utils import format as formatter
from .utils import perms
from .utils.config import Config

class Regex:
  def __init__(self, bot):
    self.bot = bot
    self.replacements = Config('configs/replace.json')

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
  async def _add(self, ctx, *, regex):
    """adds a new replacement
    Format `s/old/new/`
    """
    
    print(regex)
    
    #Find requested replacement
    rep = get_match(regex)
    
    #ensure that replace was found before proceeding
    if not rep:
      await self.bot.say(formatter.error('Could not find valid regex'))
      return
      
    #check regex for validity
    try:
      re.compile(rep.group(2))
    except re.error:
      await self.bot.say(formatter.error('regex is invalid'))
      return
    
    #make sure regex is not too broad
    if bad_re(rep.group(2)):
      await self.bot.say(formatter.error('regex is too broad'))
      return
    
    #check that regex does not already exist
    if rep.group(2) in self.replacements:
      await self.bot.say(formatter.error('regex already exists'))
      return
    
    self.replacements[rep.group(2)] = [rep.group(4), ctx.message.author.id]
    await self.bot.say(formatter.ok())
  
  @rep.command(name='edit', pass_context=True)
  async def _edit(self, ctx, *, regex):
    """edits an existing replacement
    Format `s/old/new/`
    """
    
    #Find requested replacement
    rep = get_match(regex)
    
    #ensure that replace was found before proceeding
    if not rep:
      await self.bot.say(formatter.error('Could not find valid regex'))
      return
    
    #check regex for validity
    try:
      re.compile(rep.group(2))
    except re.error:
      await self.bot.say(formatter.error('regex is invalid'))
      return
    
    #make sure regex is not too broad
    if bad_re(rep.group(2)):
      await self.bot.say(formatter.error('regex is too broad'))
      return
    
    #ensure that replace was found before proceeding
    if rep.group(2) not in self.replacements:
      await self.bot.say(formatter.error('Regex not in replacements.'))
      return
    
    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[rep.group(2)][1] \
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot edit')
    
    self.replacements[rep.group(2)] = [rep.group(4), ctx.message.author.id]
    await self.bot.say(formatter.ok())
  
  @rep.command(name='remove', aliases=['rm'], pass_context=True)
  async def _rm(self, ctx, *, pattern):
    """remove an existing replacement"""
    
    pattern = re.sub('^(`)?\\(\\?[^\\)]*\\)', '\\1', pattern)
    
    #ensure that replace was found before proceeding
    if pattern not in self.replacements:
      if re.search('^`.*`$', pattern) and pattern[1:-1] in self.replacements:
        pattern = pattern[1:-1]
      else:
        await self.bot.say(formatter.error('Regex not in replacements.'))
        return
    
    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[pattern][1] \
       and not perms.check_permissions(ctx, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot delete')
    
    self.replacements.pop(pattern)
    await self.bot.say(formatter.ok())
  
  @rep.command(name='list', aliases=['ls'])
  async def _ls(self):
    """list existing replacements"""
    msg = ''
    
    for rep in self.replacements:
      msg += '\"{}\" -> \"{}\"\n'.format(rep, self.replacements[rep][0])
    msg = msg[:-1]
    
    await self.bot.say(formatter.code(msg))
  
def get_match(string):
  pattern = r'^s{0}(\(\?i\))?(.*?[^\\](\\\\)*){0}(.*?[^\\](\\\\)*){0}g?$'
  sep = re.search('^s(.)', string)
  if not sep or len(sep.groups()) < 1 or len(sep.group(1)) != 1:
    return None
  return re.match(pattern.format(sep.group(1)), string)
  
def bad_re(string):
  string_a = re.sub(r'\(\?[^\)]*\)', '', string)
  string_a = re.sub(r'.\?', '', string_a)
  string_a = re.sub(r'\[[^\]]*\]', '', string_a)
  string_a = re.sub(r'(?!\\)[\.\?\+\*\{\}\)\(\[\]\^\$]', '', string_a)
  string_a = re.sub('\\\\[bSDWBQEs]', '', string_a)
  
  return len(string_a) < 3

def setup(bot):
  bot.add_cog(Regex(bot))
