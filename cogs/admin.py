from discord.ext import commands
import discord
import inspect
import asyncio
import git
import sys
from includes.utils import perms
from includes.utils import format as formatter
import logging

# to expose to the eval command
import datetime
from collections import Counter
from includes.utils.config import Config
from includes.utils import discord_helper as dh

logger = logging.getLogger('navi.admin')

class Admin(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(hidden=True)
  @perms.has_perms(administrator=True)
  async def disable(self, ctx, *, cog_name : str):
    """Disables a cog in this guild"""
    if not self.bot.get_cog(cog_name):
      await ctx.send(formatter.error(f'cog "{cog_name}" not found'))
      return

    if cog_name == 'Admin':
      await ctx.send(formatter.error(f"You can't disable the Admin cog"))
      return

    perm_conf = Config('configs/perms.json')
    disabled = perm_conf.get('disabled').setdefault(
      str(ctx.message.guild.id),
      perm_conf.get('disabled_default', [])
    )

    disabled.append(cog_name)
    perm_conf.save()

    await ctx.send(formatter.ok())

  @commands.command(hidden=True)
  @perms.has_perms(administrator=True)
  async def enable(self, ctx, *, cog_name : str):
    """Enables a cog in this guild"""
    perm_conf = Config('configs/perms.json')
    disabled = perm_conf.get('disabled').setdefault(
      str(ctx.message.guild.id),
      perm_conf.get('disabled_default', [])
    )

    if cog_name not in disabled:
      await ctx.send(formatter.error(f'cog "{cog_name}" not disabled'))
    else:
      disabled.remove(cog_name)
      perm_conf.save()
      await ctx.send(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def load(self, ctx, *, module : str):
    """Loads a module."""
    async with ctx.typing():
      try:
        self.bot.load_extension(module)
      except Exception as e:
        logger.exception('could not load cog')
        await ctx.send('\N{PISTOL}')
        await ctx.send('{}: {}'.format(type(e).__name__, e))
      else:
        await ctx.send(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def unload(self, ctx, *, module : str):
    """Unloads a module."""
    async with ctx.typing():
      try:
        self.bot.unload_extension(module)
      except Exception as e:
        logger.exception('could not unload cog')
        await ctx.send('\N{PISTOL}')
        await ctx.send('{}: {}'.format(type(e).__name__, e))
      else:
        await ctx.send(formatter.ok())

  @commands.command(name='reload', hidden=True)
  @perms.is_owner()
  async def _reload(self, ctx, *, module : str):
    """Reloads a module."""
    async with ctx.typing():
      try:
        self.bot.unload_extension(module)
        self.bot.load_extension(module)
      except Exception as e:
        logger.exception('could not reload cog')
        await ctx.send('\N{PISTOL}')
        await ctx.send('{}: {}'.format(type(e).__name__, e))
      else:
        await ctx.send(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def update(self, ctx):
    async with ctx.typing():
      loop = asyncio.get_event_loop()
      g = git.cmd.Git('.')
      await loop.run_in_executor(
        None,
        g.execute,
        ['git','reset','HEAD~1','--hard']
      )
      await loop.run_in_executor(None, g.pull)
      await ctx.send(formatter.ok('restarting'))

    await self.bot.logout()
    loop.stop()
    #concurrent.futures.ProcessPoolExecutor().shutdown()
    sys.exit()

  @commands.command(hidden=True)
  @perms.is_owner()
  async def debug_on(self, ctx):
    logging.getLogger('navi').setLevel(logging.DEBUG)
    logging.getLogger('discord').setLevel(logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.DEBUG)
    ctx.bot.loop.set_debug(True)
    await ctx.send(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def debug_off(self, ctx):
    logging.getLogger('navi').setLevel(logging.INFO)
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    ctx.bot.loop.set_debug(False)
    await ctx.send(formatter.ok())

  @commands.command(hidden=True)
  @perms.is_owner()
  async def reboot(self, ctx):
    loop = asyncio.get_event_loop()
    await self.bot.logout()
    loop.stop()
    g = git.cmd.Git('.')
    g.execute(['sudo', 'reboot'])
    sys.exit()


  @commands.command(hidden=True)
  @perms.is_owner()
  async def debug(self, ctx, *, code : str):
    """Evaluates code."""
    code = code.strip('` ')
    result = None

    env = {
      'bot':     self.bot,
      'ctx':     ctx,
      'message': ctx.message,
      'server':  ctx.message.guild,
      'channel': ctx.message.channel,
      'author':  ctx.message.author
    }

    env.update(globals())

    async with ctx.typing():
      try:
        result = eval(code, env)
        if inspect.isawaitable(result):
          result = await result
      except Exception as e:
        await ctx.send(formatter.code(type(e).__name__ + ': ' + str(e)))
        return

      await ctx.send(formatter.code(result, 'py'))

def setup(bot):
  bot.add_cog(Admin(bot))
