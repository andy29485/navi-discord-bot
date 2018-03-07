#!/usr/bin/env python3

import re
import json
import aiohttp
import asyncio
import logging
import html2text
import asyncjisho
from lxml import etree
from urllib.parse import parse_qs
from urllib import parse as urlencode

from includes.utils import format as formatter

logger = logging.getLogger('navi.internet')
jisho  = asyncjisho.Jisho()

async def google(query):
  entries  = await get_search_entries(query)
  next_two = '\n'.join(entries[1:3])
  if next_two:
    message = f'{entries[0]}\n\n**See also:**\n{next_two}'
  else:
    message = entries[0]
  return message

def lmgtfy(search_terms):
  query = urlencode.urlencode({"s":"d", "q":search_terms})
  return f'https://lmgtfy.com/?{query}'

async def jisho_search(search):
  result = await jisho.lookup(search)
  if len(result) == 0:
    return None
  else:
    result = next(result)

  #TODO use https once jisho finially implements it

  em = discord.Embed(title=search, color=discord.Color.green(),
                     url='http://jisho.org/search/{}'.format(search)
  )

  # add basic info if there
  em.add_field(name='**English**', value=', '.join(result.get('english')))
  if result.get('parts_of_speech'):
    em.add_field(name='**Part**', value=', '.join(result['parts_of_speech']))

  # divider in the embed
  em.add_field(name=u'\u200b', value=u'\u200b', inline=True)

  if result.get('words'):
    em.add_field(name='**Words**', value=', '.join(result['words']))
  if result.get('readings'):
    em.add_field(name='**Readings**', value=', '.join(result['readings']))

  return em

async def get_search_entries(query):
  url_d = 'http://api.duckduckgo.com/'
  url_g = 'https://www.google.com/search'
  params_d = {
    'q'             : query,
    'format'        :'json',
    'pretty'        : 0,
    'skip_disambig' :1
  }
  params_g = {
    'q'    : query,
    'safe' : 'off'
  }
  headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0)'
  }

  # list of entries
  entries = []

  async with aiohttp.ClientSession() as session:
    async with session.get(url_g, params=params_g, headers=headers) as resp:
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


        html    = etree.tostring(entry_node).decode('utf-8')
        summary = html2text.html2text(html) # convert html to markdown
        url     = parse_qs(url[5:])['q'][0]

        rep = {
          '&amp;'    : '&',
          '[\\s\n]+' : ' '
        }

        for r in rep:
          summary = re.sub(r, rep[r], summary)

        # if I ever cared about the description, this is how
        entries.append('<{}>\n{}\n'.format(url, summary))
  return entries
