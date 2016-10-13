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
from .utils.find import find
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
  @perms.is_owner()
  async def img(self, *search):
    if 'path' not in self.conf or not os.path.exists(self.conf['path']):
      await self.bot.say('path does not exist')
    
    try:
      path = find(self.conf['path'], '*'.join(search))
    except:
      path = ''
    
    if path in self.conf['images']:
      image_id = self.conf['images'][path]['id']
      url = self.conf['images'][path]['url']
      try:
        if self.account.thumbnail(image_id):
          await self.bot.say(url)
          return
      except:
        pass
      
    out = ''
    if path:
      image = self.account.upload(path)
      if image and image.url:
        self.conf['images'][path] = {'id':image.id, 'url':image.url}
        self.conf.save()
        out = image.url
      else:
        out = 'could not upload image'
    else:
      out = 'could not find anything matching: `{}`'.format(search)
    await self.bot.say(out)

def setup(bot):
  bot.add_cog(AZ(bot))
