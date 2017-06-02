#!/usr/bin/env python3

import re
import random
import asyncio
import pybooru
from discord import Embed
from discord.ext import commands
from cogs.utils.config import Config
import cogs.utils.format as formatter

class NSFW:
  def __init__(self, bot):
    self.bot      = bot
    self.conf     = Config('configs/nsfw.json')
    if 'yandere-conf' not in self.conf:
      self.conf['yandere-conf']  = {}
    if 'danbooru-conf' not in self.conf:
      self.conf['danbooru-conf'] = {}
    self.yandere  = pybooru.Moebooru('yandere',  **self.conf['yandere-conf'])
    self.danbooru = pybooru.Danbooru('danbooru', **self.conf['danbooru-conf'])

  @commands.group(pass_context=True)
  async def nsfw(self, ctx):
    """NSFW stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))
      return

    channel = ctx.message.channel
    if 'nsfw' not in channel.name.lower() and not channel.is_private:
      await self.bot.say('not in nsfw channel')
      ctx.invoked_subcommand = None
      return

  @nsfw.command(name='danbooru', aliases=['d'])
  async def _danbooru(self, search_tags : str):
    """
      searches danbooru for an image

      usage: .nsfw danbooru tags1 tag2, tag_3, etc...
      must specify at least 1 tag
      will potentially return nsfw images
    """
    tags  = re.split(',?\\s+', search_tags)
    posts = self.danbooru.post_list(limit=1,tags=tags,random=True)
    em    = Embed()

    if not posts:
      await self.bot.say('could not find anything')
      return

    post = posts[0]

    em.title = search_tags
    em.url   = 'https://danbooru.donmai.us/posts/{}'.format(post['id'])
    u        = 'https://danbooru.donmai.us'
    if 'large_file_url' in post:
      u += post['large_file_url']
    else:
      u += post['file_url']
    em.set_image(url=u)
    if post['tag_string']:
      em.set_footer(text=post['tag_string'])

    await self.bot.say(embed=em)

  @nsfw.command(name='yandere', aliases=['y'])
  async def _yandre(self, search_tags : str):
    """
      searches yande.re for an image

      usage: .nsfw yandere tags1 tag2, tag_3, etc...
      must specify at least 1 tag
      will potentially return nsfw images
    """
    tags  = re.split(',?\\s+', search_tags)
    posts = self.yandere.post_list(limit=100,tags=tags,random=True)
    em    = Embed()

    post = random.choice(posts)

    if not post:
      await self.bot.say('could not find anything')
      return

    em.title = search_tags
    em.url   = 'https://yande.re/post/show/{}'.format(post['id'])
    u        = post['file_url']
    em.set_image(url=u)
    if post['tags']:
      em.set_footer(text=post['tags'])

    await self.bot.say(embed=em)

def setup(bot):
  bot.add_cog(NSFW(bot))
