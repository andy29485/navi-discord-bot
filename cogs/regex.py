#!/usr/bin/env python3

import asyncio
from discord.ext import commands

from includes.regex import Regex as RegexRes
from cogs.utils import format as formatter

class RegexCog:
  def __init__(self, bot):
    self.bot   = bot
    self.regex = RegexRes()

  @commands.group(pass_context=True)
  async def rep(self, ctx):
    """Manage replacements
    Uses a regex to replace text from users
    """
    message = None
    if self.regex.is_banned(ctx.message.author.id):
      message = formatter.error('No ')+':poi:'
      ctx.invoked_subcommand = None
    if ctx.invoked_subcommand is None:
      message = f'Error, {ctx.subcommand_passed} is not a valid command\n' + \
                 'try: `.rep list`, `.rep add`, or `.rep remove` instead'

    if message:
      await self.bot.say(formatter.error(message))

  @rep.command(name='add', pass_context=True)
  async def _add(self, ctx, *, regex):
    """adds a new replacement
    Format `s/old/new/`
    """
    await self.bot.say(self.regex.add(regex, ctx.message.author.id))

  @rep.command(name='edit', pass_context=True)
  async def _edit(self, ctx, *, regex):
    """edits an existing replacement
    Format `s/old/new/`
    """
    await self.bot.say(self.regex.edit(regex, ctx.message.author.id))

  @rep.command(name='remove', aliases=['rm'], pass_context=True)
  async def _rm(self, ctx, *, pattern):
    """remove an existing replacement"""
    await self.bot.say(self.regex.rm(regex, ctx.message.author.id))

  @rep.command(name='list', aliases=['ls'])
  async def _ls(self):
    """list existing replacements"""
    await self.bot.say(self.regex.ls())

  async def replace(self, message):
    if message.author.bot:
      return
    if len(message.content.strip()) < 2:
      return
    if message.content.strip()[0] in self.bot.command_prefix+['?', '$']:
      return

    m = self.regex.replace(message.content)
    if m:
      await self.bot.send_message(message.channel, '*'+m)

def setup(bot):
  reg = RegexCog(bot)
  bot.add_listener(reg.replace, "on_message")
  bot.add_cog(reg)
