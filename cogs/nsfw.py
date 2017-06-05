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

    if 'update' not in self.conf:
      self.conf['update'] = {'safebooru':{'url':'https://safebooru.donmai.us'}}
      self.conf.save()
    pybooru.resources.SITE_LIST.update(self.conf['update'])

    if 'yandere-conf' not in self.conf:
      self.conf['yandere-conf']  = {}
    if 'danbooru-conf' not in self.conf:
      self.conf['danbooru-conf'] = {}
    if 'safebooru-conf' not in self.conf:
      self.conf['safebooru-conf'] = {}

    self.yandere  =  pybooru.Moebooru('yandere',  **self.conf['yandere-conf'])
    self.danbooru =  pybooru.Danbooru('danbooru', **self.conf['danbooru-conf'])
    self.safebooru = pybooru.Danbooru('safebooru',**self.conf['safebooru-conf'])

  @commands.group(pass_context=True)
  async def nsfw(self, ctx):
    """NSFW stuff"""
    channel = ctx.message.channel
    if not channel.is_private and 'nsfw' not in channel.name.lower():
      await self.bot.say(formatter.error('not in nsfw channel'))
      ctx.invoked_subcommand = None
      return

    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))
      return

  @nsfw.command(name='danbooru', aliases=['d'])
  async def _danbooru(self, *, search_tags : str = ''):
    """
      searches danbooru for an image

      usage: .nsfw danbooru tags1 tag2, tag_3, etc...
      must specify at least 1 tag
      will potentially return nsfw images
    """
    tags  = re.split(',?\\s+', search_tags)
    for i in range(len(tags)):
      if re.search('^(//|#)', tags[i]):
        tags = tags[:i]
        break

    for i in range(len(tags)):
      if re.search('^(/\\*)', tags[i]):
        for j in range(i, len(tags)):
          if re.search('^(\\*/)', tags[j]):
            break
        tags = tags[:i] + tags[j+1:]
        break

    if not tags:
      tags = ['rating:e']

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
    elif 'file_url' in post:
      u += post['file_url']
    else:
      await self.bot.say('''
              Sorry, there seems to be a premium tag in the query,
              send me $20 if you you want to search it.
      ''')
    em.set_image(url=u)
    if post['tag_string']:
      em.set_footer(text=post['tag_string'])

    await self.bot.say(embed=em)

  @nsfw.command(name='yandere', aliases=['y'])
  async def _yandre(self, *, search_tags : str):
    """
      searches yande.re for an image

      usage: .nsfw yandere tags1 tag2, tag_3, etc...
      must specify at least 1 tag
      will potentially return nsfw images
    """
    tags  = re.split(',?\\s+', search_tags)
    for i in range(len(tags)):
      if re.search('^(//|#)', tags[i]):
        tags = tags[:i]
        break

    for i in range(len(tags)):
      if re.search('^(/\\*)', tags[i]):
        for j in range(i, len(tags)):
          if re.search('^(\\*/)', tags[j]):
            break
        tags = tags[:i] + tags[j+1:]
        break

    if not tags:
      tags = ['rating:e']

    posts = self.yandere.post_list(limit=100,tags=tags)
    em    = Embed()

    if not posts:
      await self.bot.say('could not find anything')
      return

    post = random.choice(posts)

    em.title = search_tags
    em.url   = 'https://yande.re/post/show/{}'.format(post['id'])
    u        = post['file_url']
    em.set_image(url=u)
    if post['tags']:
      em.set_footer(text=post['tags'])

    await self.bot.say(embed=em)

  @commands.command(name='safebooru', aliases=['s', 'safe'])
  async def _safebooru(self, *, search_tags : str):
    """
      searches safebooru for an image

      usage: .nsfw safebooru tags1 tag2, tag_3, etc...
      must specify at least 1 tag
      will should not return nsfw images
    """
    tags  = re.split(',?\\s+', search_tags)
    for i in range(len(tags)):
      if re.search('^(//|#)', tags[i]):
        tags = tags[:i]
        break

    for i in range(len(tags)):
      if re.search('^(/\\*)', tags[i]):
        for j in range(i, len(tags)):
          if re.search('^(\\*/)', tags[j]):
            break
        tags = tags[:i] + tags[j+1:]
        break

    posts = self.safebooru.post_list(limit=1,tags=tags,random=True)
    em    = Embed()

    if not posts:
      await self.bot.say('could not find anything')
      return

    post = posts[0]

    em.title = search_tags
    em.url   = 'https://safebooru.donmai.us/posts/{}'.format(post['id'])
    u        = 'https://safebooru.donmai.us'
    if 'large_file_url' in post:
      u += post['large_file_url']
    elif 'file_url' in post:
      u += post['file_url']
    else:
      await self.bot.say('''
              Sorry, there seems to be a premium tag in the query,
              send me $20 if you you want to search it.
      ''')
    em.set_image(url=u)
    if post['tag_string']:
      em.set_footer(text=post['tag_string'])

    await self.bot.say(embed=em)

def setup(bot):
  bot.add_cog(NSFW(bot))
