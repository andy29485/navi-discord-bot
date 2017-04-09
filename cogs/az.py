#!/usr/bin/env python3

import random
import re
import requests
import asyncio
import discord
import puush
import os
from discord.ext import commands
from cogs.utils.format import *
from cogs.utils import perms
from cogs.utils import find as azfind
from cogs.utils.config import Config


that = """
╚═( ͡° ͜ʖ ͡° )═╝
..╚═(███)═╝
.╚═(███)═╝
..╚═(███)═╝
...╚═(███)═╝
....╚═(███)═╝
...╚═(███)═╝
..╚═(███)═╝
.╚═(███)═╝
╚═(███)═╝
.╚═(███)═╝
..╚═(███)═╝
...╚═(███)═╝
...╚═(███)═╝
.....╚(███)╝
.......╚(██)╝
.........(█)
..........*"""

class AZ:
  def __init__(self, bot):
    self.bot = bot
    self.conf = Config('configs/az.json')
    if 'path' not in self.conf:
      self.conf['path'] = input('Enter dir to search for: ')

    if 'key' not in self.conf:
      self.conf['key'] = input('Enter puush api key: ')
    self.account = puush.Account(self.conf['key'])

    if 'images' not in self.conf or type(self.conf['images']) != dict:
      self.conf['images'] = {}

  @commands.command()
  async def lenny(self, first=None):
    try:
      first = int(first)
      if first < 1:
        first = 1
      if first > 10:
        first = 10
    except:
      first = 1
    await self.bot.say('\n( ͡° ͜ʖ ͡° )'*first)

  @commands.command()
  async def shrug(self):
    await self.bot.say('\n¯\_(ツ)_/¯')

  @commands.command()
  async def lennytipede(self):
    await self.bot.say(code(that))

  @commands.command(pass_context=True)
  @perms.in_group('img')
  async def img(self, ctx, *search):
    if 'path' not in self.conf or not os.path.exists(self.conf['path']):
      await self.bot.say('{path} does not exist')
      return

    search = [re.sub(r'[^\w\./#\*-]+', '', i).lower() for i in search]
    for i in range(len(search)):
      if re.search('^(//|#)', search[i]):
        search = search[:i]
        break

    for i in range(len(search)):
      if re.search('^(/\\*)', search[i]):
        for j in range(i, len(search)):
          if re.search('^(\\*/)', search[j]):
            break
        search = search[:i] + search[j+1:]
        break

    loop = asyncio.get_event_loop()
    try:
      f = loop.run_in_executor(None, azfind.search, self.conf['path'], search)
      path = await f
    except:
      path = ''

    if not path or not path.strip():
      await self.bot.send_message(ctx.message.channel, "couldn't find anything matching: `{}`".format(search))
      return

    try:
      future_url = loop.run_in_executor(None, self.get_url, path)
      url = await future_url
    except:
      url = 'There was an error uploading the image, ' + \
            'but at least I didn\'t crash :p'
    await self.bot.say(url)

  def confirm_img(self, urls):
    for url in urls.split('\n'):
      if url and requests.get(url, timeout=2).status_code != 200:
        return False
    return True

  def get_url(self, path):
    if path in self.conf['images']:
      urls = self.conf['images'][path]['url']
      try:
        if self.confirm_img(urls):
          return urls
      except:
        pass

    out = ''
    if path.rpartition('.')[2].lower() in ['zip', 'cbz']:
      files = azfind.extract(path)
      if files:
        out = self.upload(files, path)
        for f in files:
          os.remove(f)
        os.rmdir(os.path.dirname(files[0]))
      else:
        out = 'archive found... but empty'
      return out
    else:
      return self.upload([path])

  def upload(self, paths, p=None):
    if not p:
      p = paths[0]
    urls = ''
    for path in paths:
      for i in range(3):
        try:
          image = self.account.upload(path)
          if image and image.url:
            urls += image.url + '\n'
            break
        except ValueError:
          pass
      else:
        return 'could not upload image'
    self.conf['images'][p] = {'url':urls}
    self.conf.save()
    return urls

def setup(bot):
  bot.add_cog(AZ(bot))
