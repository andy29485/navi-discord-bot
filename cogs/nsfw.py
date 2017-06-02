#!/usr/bin/env python3

import re
import asyncio
import pybooru
from discord import Embed
from discord.ext import commands
from cogs.utils.config import Config

class Nsfw:
  def __init__(self, bot):
    self.bot      = bot
    self.conf     = Config('configs/nsfw.json')
    if 'yandere-conf' not in self.conf:
      self.conf['yandere-conf']  = {}
    if 'danbooru-conf' not in self.conf:
      self.conf['danbooru-conf'] = {}
    self.yandere  = pybooru.Moebooru('yandere',  **self.conf['yandere-conf'])
    self.danbooru = pybooru.Danbooru('danbooru', **self.conf['danbooru-conf'])

  @commands.command(name='danbooru', aliases=['db'])
  async def _danbooru(self, search_tags : str):
    tags  = re.split(',?\\s+', search_tags)
    posts = self.danbooru.post_list(limit=1,tags=tags,random=True)
    em    = Embed()

    if not posts:
      await self.bot.say('could not find anything')
      return

    post = posts[0]

    em.title = search_tags
    em.url   = 'https://danbooru.donmai.us/posts/{}'.format(post['id'])
    em.set_image(url='https://danbooru.donmai.us'+post['large_file_url'])
    if post['tag_string']:
      em.set_footer(text=post['tag_string'])

    await self.bot.say(embed=em)


def setup(bot):
  bot.add_cog(Nsfw(bot))
