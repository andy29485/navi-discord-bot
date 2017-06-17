#!/usr/bin/env python3

import re
import asyncio
from discord.ext import commands
from cogs.utils import format as formatter
from cogs.utils import perms
from cogs.utils.config import Config

class Regex:
  def __init__(self, bot):
    self.bot = bot
    self.replacements = Config('configs/replace.json')
    self.permissions  = Config('configs/perms.json')
    if 'rep-blacklist' not in self.permissions:
      self.permissions['rep-blacklist'] = []

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

    if ctx.message.author.id in self.permissions['rep-blacklist']:
      await self.bot.say(formatter.error('No ')+':poi:')
      return

    #Find requested replacement
    rep = get_match(regex)

    #ensure that replace was found before proceeding
    if not rep:
      await self.bot.say(formatter.error('Could not find valid regex'))
      return

    p1 = formatter.escape_mentions(rep.group(2))
    p2 = formatter.escape_mentions(rep.group(4))

    #check regex for validity
    if not comp(p1, p2):
      await self.bot.say(formatter.error('regex is invalid'))
      return

    #make sure that there are no similar regexes in db
    for i in self.replacements:
      if similar(p1, i):
        r = '\"{}\" -> \"{}\"'.format(i, self.replacements[i][0])
        message = 'Similar regex already exists, delete or edit it\n{}'.format(
                   formatter.inline(r))
        await self.bot.say(formatter.error(message))
        return

    #make sure regex is not too broad
    if bad_re(p1):
      await self.bot.say(formatter.error('regex is too broad'))
      return

    #check that regex does not already exist
    if p1 in self.replacements:
      await self.bot.say(formatter.error('regex already exists'))
      return

    self.replacements[p1] = [p2, ctx.message.author.id]
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

    p1 = formatter.escape_mentions(rep.group(2))
    p2 = formatter.escape_mentions(rep.group(4))

    #check regex for validity
    if not comp(p1, p2):
      await self.bot.say(formatter.error('regex is invalid'))
      return

    #make sure regex is not too broad
    if bad_re(p1):
      await self.bot.say(formatter.error('regex is too broad'))
      return

    #ensure that replace was found before proceeding
    if p1 not in self.replacements:
      await self.bot.say(formatter.error('Regex not in replacements.'))
      return

    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[p1][1] \
       #will uncomment next line when reps are a per server thing
       #and not perms.check_permissions(ctx.message, manage_messages=True):
       and not perms.is_owner_check(ctx.message):
        raise commands.errors.CheckFailure('Cannot edit')

    self.replacements[p1] = [p2, ctx.message.author.id]
    await self.bot.say(formatter.ok())

  @rep.command(name='remove', aliases=['rm'], pass_context=True)
  async def _rm(self, ctx, *, pattern):
    """remove an existing replacement"""

    #pattern = re.sub('^(`)?\\(\\?[^\\)]*\\)', '\\1', pattern)
    pattern = formatter.escape_mentions(pattern)

    #ensure that replace was found before proceeding
    if pattern not in self.replacements:
      if re.search('^`.*`$', pattern) and pattern[1:-1] in self.replacements:
        pattern = pattern[1:-1]
      else:
        await self.bot.say(formatter.error('Regex not in replacements.'))
        return

    #check if they have correct permissions
    if ctx.message.author.id != self.replacements[pattern][1] \
       and not perms.check_permissions(ctx.message, {'manage_messages':True}):
        raise commands.errors.CheckFailure('Cannot delete')

    self.replacements.pop(pattern)
    self.replacements.save()
    await self.bot.say(formatter.ok())

  @rep.command(name='list', aliases=['ls'])
  async def _ls(self):
    """list existing replacements"""
    msg = ''

    for rep in self.replacements:
      msg += '\"{}\" -> \"{}\"\n'.format(rep, self.replacements[rep][0])
    msg = msg[:-1]

    await self.bot.say(formatter.code(msg))

  async def replace(self, message):
    if message.author.bot:
      return
    if len(message.content.strip()) < 2:
      return
    if message.content.strip()[0] in self.bot.command_prefix+['?', '$']:
      return

    m = message.content
    for i in self.replacements:
      m = re.sub(r'(?i)\b{}\b'.format(i), self.replacements[i][0], m)

    if m.lower() != message.content.lower():
      await self.bot.send_message(message.channel, '*'+m)

def get_match(string):
  pattern = r'^s{0}(\(\?i\))?(.*?[^\\](\\\\)*){0}(.*?[^\\](\\\\)*){0}g?$'
  sep = re.search('^s(.)', string)
  if not sep or len(sep.groups()) < 1 or len(sep.group(1)) != 1:
    return None
  return re.match(pattern.format(sep.group(1)), string)

def simplify(pattern):
  out = set()
  reps = [r'(?!\\)[\.\?\+\*]',
          r'\\[bSDWBQEs]',
          r'(?!\\)[\)\(\[\]]',
          r'\(\?[^\)]*\)',
          r'\(\?[^\)]*\)',
          r'.\?',
          r'\[[^\]]*\]',
          r'\{[^\}]*\}',
          r'\s+']
  string_a = pattern
  for r in reps:
    string_a = re.sub(r, '', string_a)
    out.add(re.sub(r, '', pattern))
    out.add(string_a)
  return out

def similar(pattern1, pattern2):
  for sim1 in simplify(pattern1):
    for sim2 in simplify(pattern2):
      if (sim1.lower() == sim2.lower() or \
         re.search(r'(?i)\b{}\b'.format(pattern1), sim2) or \
         re.search(r'(?i)\b{}\b'.format(pattern2), sim1) or \
         (comp(sim1, sim2) and re.search(r'(?i)\b{}\b'.format(sim1), sim2)) or\
         (comp(sim2, sim1) and re.search(r'(?i)\b{}\b'.format(sim2), sim1))):
          return True
  return False

def bad_re(pattern):
  return max(len(s) for s in simplify(pattern)) < 3

def comp(regex, replace=''):
  try:
    re.sub(regex, replace, '')
    return True
  except:
    return False

def setup(bot):
  reg = Regex(bot)
  bot.add_listener(reg.replace, "on_message")
  bot.add_cog(reg)
