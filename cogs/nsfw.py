#!/usr/bin/env python3

import re
import asyncio
import pybooru
from discord import Embed
from discord.ext import commands

class Nsfw:
  def __init__(self, bot):
    self.bot   = bot
    self.yandere = pybooru.Moebooru('yandere')

  @commands.command()
  async def yandere(self, search_tags : str):
    tags = re.split(',?\\s+', search_tags)
    post = self.yandere.post_list(limit=1,tags=tags,random=True)
    em   = Embed()

    if not post:
      await self.bot.say('could not find anything')
      return

    post = post[0]

    em.title = search_tags
    em.url   = 'https://yande.re/post/show/{}'.format(post['id'])
    em.set_image(post['file_url'])
    if post['tags']:
      em.set_footer(text=post['tags'])

    self.bot.say(embed=em)


def setup(bot):
  bot.add_cog(Nsfw(bot))
