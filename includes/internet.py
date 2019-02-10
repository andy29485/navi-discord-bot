#!/usr/bin/env python3

import re
import json
import aiohttp
import asyncio
import discord
import logging
import pixivpy3
import html2text
import asyncjisho
import datetime
from lxml import etree
from urllib.parse import parse_qs
from urllib import parse as urlencode

from includes.utils.config import Config
from includes.utils import format as formatter

logger = logging.getLogger('navi.internet')
conf = Config('configs/internet.json')
jisho  = asyncjisho.Jisho()
papi = pixivpy3.AppPixivAPI()

PIXIV_URL_PAT = re.compile(
  r'(https?://)?((www|m|touch|ssl)\.)?pixiv\.(co\.jp|org|com|net)/('
    r'[/\.&\w\?=]+[&\?]illust_id=(?P<illust_id>\d+)|'
    r'member(_illust)?.php[/\.&\w\?=]*[&\?]id=(?P<member_id>\d+)'
  ')'
)

def _pixiv_auth():
  papi.auth(refresh_token=conf.get('pixiv_token'))

if not conf.get('saucenao_token'):
  conf['saucenao_token'] = input('Enter SauceNAO token: ')
  conf.save()

if not conf.get('pixiv_token'):
  uname = input('Enter Pixiv username: ')
  pword = input('Enter Pixiv password: ')
  token = papi.login(uname,pword).get('response',{}).get('refresh_token')
  if not token:
    papi = None
  else:
    conf['pixiv_token'] = token
    conf.save()
else:
  _pixiv_auth()

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
    'skip_disambig' : 1
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

async def _pixiv_illust(message, id):
  try:
    async with message.channel.typing():
      files = []
      illust = papi.illust_detail(id)
      if 'error' in illust:
        _pixiv_auth()
        illust = papi.illust_detail(id)
      illust = illust.illust
      urls = [img.image_urls.large for img in (illust.meta_pages or [illust])]

      for i,url in enumerate(urls):
        r = papi.requests_call(
          'GET',
          url,
          headers={ 'Referer': 'https://app-api.pixiv.net/' },
          stream=True
        )
        # TODO - ugoira
        ext = url.rpartition('.')[2]
        files.append(discord.File(r.raw, filename=f'{id}-{i:03}.{ext}'))

      tags = ', '.join(sorted(t.name for t in illust.tags))

      em = discord.Embed()
      em.title = illust.title
      em.description = illust.caption
      em.timestamp = datetime.datetime.fromisoformat(illust.create_date)
      em.colour = discord.Colour.blue()
      em.add_field(name='Tags:', value=tags)
      em.set_author(
        name=illust.user.name,
        url=f'https://www.pixiv.net/member.php?id={illust.user.id}',
        icon_url=(list(illust.user.profile_image_urls.values()) or [None])[0]
      )
      em.url = (
        'https://www.pixiv.net/member_illust.php?'
        f'mode=medium&illust_id={id}'
      )

      await message.channel.send(embed=em)
      # Send images in chunks of 10 - does not work b/c discord change order
      #for files_chunk in [files[i:i+10] for i in range(0, len(files), 10)]:
      #  await message.channel.send(files=files_chunk)
      for file in files:
        await message.channel.send(file=file)

  except:
    logger.exception(f'pixiv illust id: {id} - {illust}')

async def _pixiv_member(message, id):
  return
  user = papi.user_detail(id)
  em = discord.Embed()
  em.title = illust.title
  em.description = illust.caption
  em.timestamp = datetime.datetime.fromisoformat(illust.create_date)
  em.colour = discord.Colour.blue()
  em.add_field(name='Tags:', value=tags)
  em.set_author(
    name=illust.user.name,
    url=f'https://www.pixiv.net/member.php?id={illust.user.id}',
    icon_url=(list(illust.user.profile_image_urls.values()) or [None])[0]
  )
  em.url = (
    'https://www.pixiv.net/member_illust.php?'
    f'mode=medium&illust_id={id}'
  )

async def pixiv_process(message):
  if not papi: return False

  for match in PIXIV_URL_PAT.finditer(message.content):
    if match.group('illust_id'):
      await _pixiv_illust(message, match.group('illust_id'))
    elif match.group('member_id'):
      await _pixiv_member(message, match.group('member_id'))

async def get_sauce(url):
  return # TODO
  if not conf.get('saucenao_token'):
    return formatter.error('No API token')

  params = {
    'output_type': 2, # JSON
    'db': 999,
    'api_key': conf.get('saucenao_token'),
    'url': url
  }

  resp = requests.get('https://saucenao.com/search.php', params)
