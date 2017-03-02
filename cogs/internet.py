#!/usr/bin/env python3

import asyncio
from discord.ext import commands
from .utils import format as formatter
import aiohttp
import html2text
from urllib.parse import parse_qs
from lxml import etree

class Search:
  def __init__(self, bot):
    self.bot = bot

  @commands.command(name='duckduckgo', aliases=['ddg', 'd', 'g'])
  async def google(self, *, query):
    """
    Searches DuckDuckGo and gives you top results.

    Google had too many licencing issues
    and the `g` alias is kept for convinece
    """
    try:
      entries = await self.get_search_entries(query)
    except RuntimeError as e:
      await self.bot.say(str(e))
    else:
      next_two = entries[1:3]
      if next_two:
        formatted = '\n'.join(map(lambda x: '%s' % x, next_two))
        msg = '{}\n\n**See also:**\n{}'.format(entries[0], formatted)
      else:
        msg = entries[0]

      await self.bot.say(msg)

  async def get_search_entries(self, query):
    url = 'http://api.duckduckgo.com/'
    params = {
      'q'      : query,
      'format' :'json',
      'pretty' :0
    }
    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0)'
    }

    # list of entries
    entries = []


    async with aiohttp.get(url, params=params, headers=headers) as resp:
      if resp.status != 200:
        raise RuntimeError('DuckDuckGo somehow failed to respond.')

      results = resp.json()

      if results['Answer']:
        entries.append(results['Answer'])
      for result in results['Results'] + results['RelatedTopics']:
        summary = html2text.html2text(result['Result']).replace('\n', ' ')
        url     = result(result['FirstURL'])
        summery = re.sub(r'^\[[^\]]*\]\([^\)]*\) \\*- ', '', summery)

        # if I ever cared about the description, this is how
        entries.append('<{}>\n{}\n'.format(url, summary))
    return entries

def setup(bot):
  bot.add_cog(Search(bot))
