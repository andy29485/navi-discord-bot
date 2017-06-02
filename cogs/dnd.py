#!/usr/bin/env python3

import asyncio
from discord.ext import commands
from cogs.utils.config import Config

class DnD:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/dnd.json')

  @commands.command(pass_context=True)
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
    await self.bot.say(entire_message)

def setup(bot):
  d = DnD(bot)
  bot.add_cog(d)
