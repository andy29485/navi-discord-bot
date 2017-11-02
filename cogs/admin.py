from discord.ext import commands
import discord
import inspect
import asyncio
import git
import sys
from cogs.utils import perms
from cogs.utils import format as formatter
import logging

# to expose to the eval command
import datetime
from collections import Counter
from cogs.utils.config import Config
from cogs.utils import discord_helper as dh

logger = logging.getLogger('navi')

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
    loop = asyncio.get_event_loop()
    g = git.cmd.Git('.')
    await loop.run_in_executor(None,g.execute,['git','reset','HEAD~1','--hard'])
    await loop.run_in_executor(None,g.pull)
    await self.bot.say(formatter.ok('restarting'))
    await self.bot.logout()
    loop.stop()
    #concurrent.futures.ProcessPoolExecutor().shutdown()
    sys.exit()

  @commands.command(hidden=True)
  @perms.is_owner()
  async def debug_on(self):
    logger.setLevel(logging.DEBUG)
    await self.bot.say(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def debug_off(self):
    logger.setLevel(logging.INFO)
    await self.bot.say(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def reboot(self):
    loop = asyncio.get_event_loop()
    await self.bot.logout()
    loop.stop()
    g = git.cmd.Git('.')
    g.execute(['sudo', 'reboot'])
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
