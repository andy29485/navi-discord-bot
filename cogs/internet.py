#!/usr/bin/env python3

import asyncio
import discord
from discord.ext import commands

import includes.internet as internet

class Search:
  def __init__(self, bot):
    self.bot   = bot

  @commands.command(name='search', aliases=['ddg', 'd', 'g'])
  async def google(self, ctx, *, query):
    """
    Searches DuckDuckGo and Google and gives you top results.
    """
    await ctx.send(await internet.google(query))

  @commands.command(name='jisho', aliases=['j'])
  async def jisho(self, ctx, context, *, search: str):
    result = await internet.jisho_search(search)
    if not result:
      await ctx.send('No results found')
    else:
      await ctx.send(embed=result)

  @commands.command()
  async def lmgtfy(self, ctx, *, search_terms : str):
    """Creates a lmgtfy link"""
    await ctx.send(internet.lmgtfy(search_terms))

def setup(bot):
  bot.add_cog(Search(bot))
