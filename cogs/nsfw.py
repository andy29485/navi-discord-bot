#!/usr/bin/env python3

import re
import random
import asyncio
import logging
import pybooru
from discord import Embed
from discord.ext import commands
from cogs.utils.config import Config
import cogs.utils.format as formatter
from cogs.utils import discord_helper as dh

logger = logging.getLogger('navi.nsfw')

class NSFW:
  def __init__(self, bot):
    self.bot      = bot
    self.loop     = bot.loop
    self.conf     = Config('configs/nsfw.json')

    if 'update' not in self.conf:
      self.conf['update'] = {
        'safebooru':{'url':'https://safebooru.donmai.us'},
        'lolibooru':{'url':'https://lolibooru.moe'}
      }
      self.conf.save()
    pybooru.resources.SITE_LIST.update(self.conf['update'])

    if 'yandere-conf' not in self.conf:
      self.conf['yandere-conf']  = {}
    if 'danbooru-conf' not in self.conf:
      self.conf['danbooru-conf'] = {}
    if 'safebooru-conf' not in self.conf:
      self.conf['safebooru-conf'] = {}
    if 'lolibooru-conf' not in self.conf:
      self.conf['lolibooru-conf'] = {}

    self.yandere  =  pybooru.Moebooru('yandere',  **self.conf['yandere-conf'])
    self.danbooru =  pybooru.Danbooru('danbooru', **self.conf['danbooru-conf'])
    self.lolibooru = pybooru.Moebooru('lolibooru',**self.conf['lolibooru-conf'])
    self.safebooru = pybooru.Danbooru('safebooru',**self.conf['safebooru-conf'])

  @commands.group(pass_context=True)
  async def nsfw(self, ctx):
    """NSFW stuff"""
    channel = ctx.message.channel
    # ensure that the current channel is marked as nsfw
    if not channel.is_private and 'nsfw' not in channel.name.lower():
      await self.bot.say(formatter.error('not in nsfw channel'))
      ctx.invoked_subcommand = None
      return

    # if user misstyped or does not know what they are doing, complain
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))
      return

  @nsfw.command(name='danbooru', aliases=['d'])
  async def _danbooru(self, *, search_tags : str = ''):
    """
      searches danbooru for an image

      usage: .nsfw danbooru [num] tags1 tag2, tag_3, etc...
      (optional) num: number of posts to show [1,5]
      if no tags are given, rating:e is assumed
      will potentially return nsfw images
    """
    tags = re.split(',?\\s+', search_tags)
    tags = dh.remove_comments(tags)

    if len(tags) > 1 and re.match('\\d+$', tags[0]):
      num = min(5, max(1, int(tags[0])))
      tags = tags[1:]
    else:
      num = 1

    if not tags:
      tags = ['rating:e']

    tags  = ' '.join(tags)
    get   = lambda: self.danbooru.post_list(
                             limit  = num,
                             tags   = tags,
                             random = True
    )
    posts = await self.loop.run_in_executor(None, get)

    if not posts:
      await self.bot.say('could not find anything')
      return

    for post in posts:
      em    = Embed()
      em.title = search_tags or 'rating:e'
      em.url   = 'https://danbooru.donmai.us/posts/{}'.format(post['id'])
      u        = 'https://danbooru.donmai.us'
      if 'large_file_url' in post:
        u += post['large_file_url']
      elif 'file_url' in post:
        u += post['file_url']
      else:
        await self.bot.say('''
                Sorry, there seems to be a premium tag in the image,
                send me $20 if you you want to search it.
        ''')
      em.set_image(url=u)
      if post['tag_string']:
        em.set_footer(text=post['tag_string'])

      await self.bot.say(embed=em)

  @nsfw.command(name='lolibooru', aliases=['l'])
  async def _lolibooru(self, *, search_tags : str = ''):
    """
      searches lolibooru for an image

      usage: .nsfw lolibooru [num] tags1 tag2, tag_3, etc...
      (optional) num: number of posts to show [1,5]
      if no tags are given, rating:e is assumed
      will potentially return nsfw images
    """
    tags = re.split(',?\\s+', search_tags)
    tags = dh.remove_comments(tags)

    if len(tags) > 1 and re.match('\\d+$', tags[0]):
      num = min(5, max(1, int(tags[0])))
      tags = tags[1:]
    else:
      num = 1

    if not tags:
      tags = ['rating:e']

    tags  = ' '.join(tags)
    get   = lambda: self.lolibooru.post_list(
                           limit = 100,
                           tags  = tags
    )
    posts = await self.loop.run_in_executor(None, get)

    if not posts:
      await self.bot.say('could not find anything')
      return

    for i in range(num):
      if not posts:
        break
      post = random.choice(posts)
      posts.remove(post)
      em    = Embed()
      em.title = search_tags or 'rating:e'
      em.url   = 'https://lolibooru.moe/post/show/{}'.format(post['id'])
      u        = post['file_url'].replace(' ', '%20')
      em.set_image(url=u)
      if post['tags']:
        em.set_footer(text=post['tags'])

      await self.bot.say(embed=em)

  @nsfw.command(name='yandere', aliases=['y'])
  async def _yandre(self, *, search_tags : str = '' or 'rating:e'):
    """
      searches yande.re for an image

      usage: .nsfw yandere [num] tags1 tag2, tag_3, etc...
      (optional) num: number of posts to show [1,5]
      if no tags are given, rating:e is assumed
      will potentially return nsfw images
    """
    tags = re.split(',?\\s+', search_tags)
    tags = dh.remove_comments(tags)

    if len(tags) > 1 and re.match('\\d+$', tags[0]):
      num = min(5, max(1, int(tags[0])))
      tags = tags[1:]
    else:
      num = 1

    if not tags:
      tags = ['rating:e']

    tags  = ' '.join(tags)
    get   = lambda: self.yandere.post_list(
                           limit = 100,
                           tags  = tags
    )
    posts = await self.loop.run_in_executor(None, get)

    if not posts:
      await self.bot.say('could not find anything')
      return

    for i in range(num):
      if not posts:
        break
      post = random.choice(posts)
      posts.remove(post)
      em    = Embed()
      em.title = search_tags or 'rating:e'
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

      usage: .safebooru [num] tags1 tag2, tag_3, etc...
      (optional) num: number of posts to show [1,5]
      at least 1 tag must be specified
      will potentially return nsfw images
    """
    tags = re.split(',?\\s+', search_tags)
    tags = dh.remove_comments(tags)

    if len(tags) > 1 and re.match('\\d+$', tags[0]):
      num = min(5, max(1, int(tags[0])))
      tags = tags[1:]
    else:
      num = 1

    tags  = ' '.join(tags)
    get   = lambda: self.safebooru.post_list(
                           limit  = num,
                           tags   = tags,
                           random = True
    )
    posts = await self.loop.run_in_executor(None, get)

    if not posts:
      await self.bot.say('could not find anything')
      return

    for post in posts:
      em    = Embed()
      em.title = search_tags
      em.url   = 'https://safebooru.donmai.us/posts/{}'.format(post['id'])
      u        = 'https://safebooru.donmai.us'
      if 'large_file_url' in post:
        u += post['large_file_url']
      elif 'file_url' in post:
        u += post['file_url']
      else:
        await self.bot.say('''
                Sorry, there seems to be a premium tag in the image,
                send me $20 if you you want to search it.
        ''')
      em.set_image(url=u)
      if post['tag_string']:
        em.set_footer(text=post['tag_string'])

      await self.bot.say(embed=em)

def setup(bot):
  bot.add_cog(NSFW(bot))
