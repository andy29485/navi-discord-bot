#!/usr/bin/env python3

import random
import re
import asyncio
import discord
import puush
import os
from discord.ext import commands
from .utils.format import *
from .utils import perms
from .utils import find as azfind
from .utils.config import Config

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
  async def lenny(self):
    await self.bot.say('( ͡° ͜ʖ ͡° )');

  @commands.command()
  @perms.in_group('img')
  async def img(self, *search):
    if 'path' not in self.conf or not os.path.exists(self.conf['path']):
      await self.bot.say('path does not exist')

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

    try:
      path = azfind.search(self.conf['path'], search)
    except:
      raise
      path = ''

    if not path:
      await self.bot.say("couldn't find anything matching: `{}`".format(search))
      return

    await self.bot.say(self.get_url(path))

  def confirm_img(self, iids):
    for iid in iids.split('\n'):
      if not self.account.thumbnail(iid):
        return False
    return True

  def get_url(self, path):
    if path in self.conf['images']:
      image_id = self.conf['images'][path]['id']
      url      = self.conf['images'][path]['url']
      try:
        if confirm_img(image_id):
          return url
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
    iids = ''
    urls = ''
    for path in paths:
      for i in range(3):
        try:
          image = self.account.upload(path)
          if image and image.url:
            iids += image.id  + '\n'
            urls += image.url + '\n'
            break
        except ValueError:
          pass
      else:
        return 'could not upload image'
    self.conf['images'][p] = {'id':iids, 'url':urls}
    self.conf.save()
    return urls

def setup(bot):
  bot.add_cog(AZ(bot))
