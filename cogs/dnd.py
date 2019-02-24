#!/usr/bin/env python3

import asyncio
import logging
from discord.ext import commands
from includes.utils.config import Config

logger = logging.getLogger('navi.dnd')

class DnD(commands.Cog):
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/dnd.json')

  @commands.command()
  async def echo(self, ctx, *, entire_message : str):
    """
    Short description - repeats user's message

    Longer description,
    only appears when using `.help echo`
    The short description will appear in a general help
    """
    # example `.echo hello world!`
    #   ctx.message.content           # the full message `.echo hello world`
    #   entire_message                # `hello world!`
    async with ctx.typing():
      await ctx.send(f'<{ctx.message.author.name}> {entire_message}')

def setup(bot):
  d = DnD(bot)
  bot.add_cog(d)
