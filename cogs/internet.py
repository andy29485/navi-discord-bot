#!/usr/bin/env python3

import asyncio
import discord
from discord.ext import commands

import includes.internet as internet

class Search:
  def __init__(self, bot):
    self.bot   = bot

  @commands.command(name='search', aliases=['ddg', 'd', 'g'])
  async def google(self, *, query):
    """
    Searches DuckDuckGo and Google and gives you top results.
    """
    await self.bot.say(await internet.google(query))

  @commands.command(pass_context=True, name='jisho', aliases=['j'])
  async def jisho(self, context, *, search: str):
    result = await internet.jisho_search(search)
    if not result:
      await self.bot.say('No results found')
    else:
      await self.bot.say(embed=result)

  @commands.command()
  async def lmgtfy(self, *, search_terms : str):
    """Creates a lmgtfy link"""
    await self.bot.say(internet.lmgtfy(search_terms))

def setup(bot):
  bot.add_cog(Search(bot))
