from discord.ext import commands
from .utils import perms
from .utils import format as formatter
import discord
import inspect
import asyncio
import sys

# to expose to the eval command
import datetime
from collections import Counter

class Admin:
  def __init__(self, bot):
    self.bot = bot

  @commands.command(hidden=True)
  @perms.is_owner()
  async def load(self, *, module : str):
    """Loads a module."""
    try:
      self.bot.load_extension(module)
    except Exception as e:
      await self.bot.say('\N{PISTOL}')
      await self.bot.say('{}: {}'.format(type(e).__name__, e))
    else:
      await self.bot.say(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def unload(self, *, module : str):
    """Unloads a module."""
    try:
      self.bot.unload_extension(module)
    except Exception as e:
      await self.bot.say('\N{PISTOL}')
      await self.bot.say('{}: {}'.format(type(e).__name__, e))
    else:
      await self.bot.say(formatter.ok())

  @commands.command(name='reload', hidden=True)
  @perms.is_owner()
  async def _reload(self, *, module : str):
    """Reloads a module."""
    try:
      self.bot.unload_extension(module)
      self.bot.load_extension(module)
    except Exception as e:
      await self.bot.say('\N{PISTOL}')
      await self.bot.say('{}: {}'.format(type(e).__name__, e))
    else:
      await self.bot.say(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def update(self):
    import git
    loop = asyncio.get_event_loop()
    g = git.cmd.Git('.')
    loop.run_in_executor(None, g.execute, ['git', 'reset', 'HEAD~1', '--hard'])
    loop.run_in_executor(None, g.pull)
    await self.bot.say(formatter.ok('restarting'))
    loop.stop()
    #concurrent.futures.ProcessPoolExecutor().shutdown()

    sys.exit()

  @commands.command(pass_context=True, hidden=True)
  @perms.is_owner()
  async def debug(self, ctx, *, code : str):
    """Evaluates code."""
    code = code.strip('` ')
    result = None

    env = {
      'bot':     self.bot,
      'ctx':     ctx,
      'message': ctx.message,
      'server':  ctx.message.server,
      'channel': ctx.message.channel,
      'author':  ctx.message.author
    }

    env.update(globals())

    try:
      result = eval(code, env)
      if inspect.isawaitable(result):
        result = await result
    except Exception as e:
      await self.bot.say(formatter.code(type(e).__name__ + ': ' + str(e)))
      return

    await self.bot.say(formatter.code(result, 'py'))

def setup(bot):
  bot.add_cog(Admin(bot))
