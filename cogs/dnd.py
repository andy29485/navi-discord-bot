
#!/usr/bin/env python3
import asyncio
from discord.ext import commands
from .utils.config import Config

class DnD:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/dnd.json')

  @commands.command(pass_context=True)
  async def echo(self, *, ctx):
    """
    Short description - repeats user's message

    Longer description,
    only appears when using `.help echo`
    The short description will appear in a general help
    """
    message = ctx.message.content
    await self.bot.say(message)

def setup(bot):
  d = DnD(bot)
  bot.add_cog(d)
