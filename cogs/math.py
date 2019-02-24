#!/usr/bin/env python3

from discord.ext import commands
import includes.utils.format as formatter
from includes.utils import perms
from includes.math import Math
import asyncio
import discord

class MathCog(commands.Cog):
  def __init__(self, bot):
    self.bot  = bot
    self.math = Math()


  @commands.command(pass_context=True, name='math')
  async def format(self, ctx, *, formula):
    async with ctx.typing():
      try:
        f = lambda: self.math.renderLatex(
            formula, fmt='png', backgroundcolor='white'
        )
        f = await self.bot.loop.run_in_executor(None, f)
      except:
        f = None
      if f:
        await ctx.send(file=discord.File(f, 'math.png'))
      else:
        await ctx.send(formatter.error('LaTeX syntax error'))

  @commands.command(pass_context=True)
  async def graph(self, ctx, *, parameters):
    async with ctx.typing():
      try:
        f = lambda: self.math.renderGraph(
            parameters, fmt='png', backgroundcolor='white'
        )
        f = await self.bot.loop.run_in_executor(None, f)
      except:
        f = None
      if f:
        await ctx.send(file=discord.File(f, 'graph.png'))
      else:
        await ctx.send(formatter.error('Graph rendering issue'))

def setup(bot):
  math = MathCog(bot)
  bot.add_cog(math)
