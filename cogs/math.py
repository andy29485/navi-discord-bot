#!/usr/bin/env python3

from discord.ext import commands
import includes.utils.format as formatter
from includes.utils import perms
from includes.math import Math
import asyncio

class MathCog:
  def __init__(self, bot):
    self.bot  = bot
    self.math = Math()


  @commands.group(pass_context=True, name=math)
  async def _math(self, ctx, *, formula):
    if ctx.invoked_subcommand is None:
      await self.format(ctx, formula=formula)

  @_math.command(pass_context=True)
  async def format(self, ctx, *, formula):
    try:
      f = lambda: self.math.renderLatex(
          formula, fmt='png', backgroundcolor='white'
      )
      f = await self.bot.loop.run_in_executor(None, f)
    except:
      f = None
    if f:
      await self.bot.send_file(ctx.message.channel, f, filename='math.png')
    else:
      await self.bot.send_message(ctx.message.channel,
              formatter.error('LaTeX syntax error')
      )

  @_math.command(pass_context=True)
  async def graph(self, ctx, *, parameters):
    try:
      f = lambda: self.math.renderGraph(
          parameters, fmt='png', backgroundcolor='white'
      )
      f = await self.bot.loop.run_in_executor(None, f)
    except:
      f = None
    if f:
      await self.bot.send_file(ctx.message.channel, f, filename='graph.png')
    else:
      await self.bot.send_message(ctx.message.channel,
            formatter.error('Graph rendering issue')
      )

def setup(bot):
  math = MathCog(bot)
  bot.add_cog(math)
