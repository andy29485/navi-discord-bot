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

  @commands.command(name='search', aliases=['ddg', 'd', 's', 'g'])
  async def google(self, *, query):
    """
    Searches DuckDuckGo and Google and gives you top results.
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
    url_d = 'http://api.duckduckgo.com/'
    url_g = 'https://www.google.com/search'
    params_d = {
      'q'      : query,
      'format' :'json',
      'pretty' : 0
    }
    params_g = {
      'q': query,
      'safe': 'off'
    }
    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0)'
    }

    # list of entries
    entries = []


    async with aiohttp.get(url_d, params=params_d, headers=headers) as resp:
      if resp.status != 200:
        raise RuntimeError('DuckDuckGo somehow failed to respond.')

      results = await resp.json()

      if results['Answer']:
        entries.append(results['Answer'])

    async with aiohttp.get(url_g, params=params_g, headers=headers) as resp:
      if resp.status != 200:
        raise RuntimeError('Google somehow failed to respond.')

      root = etree.fromstring(await resp.text(), etree.HTMLParser())

      """
      Tree looks like this.. sort of..
      <div class="g">
          ...
          <h3>
              <a href="/url?q=<url>" ...>title</a>
          </h3>
          ...
          <span class="st">
              <span class="f">date here</span>
              summary here, can contain <em>tag</em>
          </span>
      </div>
      """

      search_nodes = root.findall(".//div[@class='g']")
      for node in search_nodes:
        entry_node = node.find(".//span[@class='st']")
        if entry_node is None or not entry_node.text:
          continue

        url_node = node.find('.//h3/a')
        if url_node is None:
          continue

        url = url_node.attrib['href']
        if not url.startswith('/url?'):
          continue

        summary = html2text.html2text(etree.tostring(entry_node).decode('utf-8'))
        url     = parse_qs(url[5:])['q'][0]

        # if I ever cared about the description, this is how
        entries.append('<{}>\n{}\n'.format(url, summary))
    return entries

def setup(bot):
  bot.add_cog(Search(bot))
