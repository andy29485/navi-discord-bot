
#!/usr/bin/env python3
import asyncio
from discord.ext import commands
from .utils.config import Config

class DnD:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/dnd.json')

  @commands.command(pass_context=True)
  async def echo(self, ctx, first_word, everything_else : str):
    """
    Short description - repeats user's message

    Longer description,
    only appears when using `.help echo`
    The short description will appear in a general help
    """
    # example `.echo hello world!`
    message = ctx.message.content # the full message `.echo hello world`
    first_word                    # just `hello`
    everything_else               # `hello world!`
    await self.bot.say(everything_else)

def setup(bot):
  d = DnD(bot)
  bot.add_cog(d)
