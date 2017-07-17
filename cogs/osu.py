#!/usr/bin/env python3

import re
import asyncio
import itertools
from discord.ext import commands
from discord import Embed
from osuapi import OsuApi, AHConnector
import osuapi
from cogs.utils import format as formatter
from cogs.utils.config import Config

class Osu:
  breatmap_sets_url_patterns = [re.compile('https://osu.ppy.sh/s/(?P<id>\\d+)')]
  breatmap_url_patterns      = [re.compile('https://osu.ppy.sh/b/(?P<id>\\d+)')]
  user_url_patterns          = [re.compile('https://osu.ppy.sh/u/(?P<id>\\d+)')]

  def __init__(self, bot):
    self.bot           = bot
    self.loop          = bot.loop
    self.conf          = Config('configs/osu.json')

    if 'api-key' not in self.conf:
      self.conf['api-key'] = input('enter osu api key: ')
    if 'watched-users' not in self.conf:
      self.conf['watched-users'] = {}
    self.conf.save()

    self.api = OsuApi(self.conf['api-key'], connector=AHConnector())

    self.loop.create_task(self.check_scores())

  async def osu_info(self, message):
    if message.author.bot:
      return

    for pattern in Osu.breatmap_sets_url_patterns:
      match = pattern.search(message.content)
      if match:
        beatmap = await self.api.get_beatmaps(beatmap_id=match.group('id'))
        em = await self.osu_embed(beatmap[0])
        await self.bot.say(embed=em)
        break

    for pattern in Osu.breatmap_url_patterns:
      match = pattern.search(message.content)
      if match:
        beatmap = await self.api.get_beatmaps(beatmapset_id=match.group('id'))
        em = await self.osu_embed(beatmap)
        await self.bot.say(embed=em)
        break

    for pattern in Osu.user_url_patterns:
      match = pattern.search(message.content)
      if match:
        user = await self.api.get_user(int(match.group('id')))
        em = await self.osu_embed(user[0])
        await self.bot.say(embed=em)
        break

  @commands.group(name='osu', aliases=["o"], pass_context=True)
  async def _osu(self, ctx):
    """
    manages osu stuff
    """
    #TODO
    pass

  @_osu.command(name='connect', aliases=['c', 'link'], pass_context=True)
  async def _osu_watch(self, ctx, osu_username : str, top_scores : int = 50):
    """
    Links a discord user account to an osu account
    osu_username - the username that you go by on https://osu.ppy.sh
    top_scores   - the top scores to report from latest [0, 100]
    """
    auth = ctx.message.author.id
    chan = ctx.message.channel.id
    user = await self.api.get_user(osu_username)
    if not users:
      await self.bot.say('could not find user')
      return

    top_scores = max(0, min(100, top_scores))
    user       = user[0].user_id
    if top_scores:
      best     = await self.api.get_user_best(user, limit=top_scores)
      best     = [(i.beatmap_id, i.score) for i in best]
    else:
      best = []

    if auth in self.conf['watched-users']:
      self.conf['watched-users'][auth]['uid']  = user
      self.conf['watched-users'][auth]['chans'].append(chan)
      self.conf['watched-users'][auth]['last'] = best

    else:
      self.conf['watched-users'][auth] = {
              'uid':   user,
              'num':   top_scores,
              'chans': [chan],
              'last':  best
      }
    self.conf.save()
    await self.bot.say(
        formatter.ok('you are now linked to: {}'.format(user.username))
    )

  async def check_scores(self):
    while self == self.bot.get_cog('Osu'):
      for duid in self.conf['watched-users']:
        ouid  = self.conf['watched-users'][duid]['uid']
        num   = self.conf['watched-users'][duid]['num']
        chans = self.conf['watched-users'][duid]['chans']
        last  = self.conf['watched-users'][duid]['last']
        name  = await self.api.get_user(user)[0].username
        best  = await self.api.get_user_best(user, limit=num)

        for i, old, new in itertools.zip_longest(range(num), last, best):
          if new.beatmap_id != old[0] or new.score > old[1]:
            em = await self.osu_embed(new)
            em.title = 'New best #{} for {} - {}'.format(i+1, name, em.title)
            for chan_id in chans:
              try:
                chan = await self.bot.get_channel(chan_id)
                await self.bot.send_message(chan, embed=em)
              except:
                pass
            break
        else:
          continue
        best = [(i.beatmap_id, i.score) for i in best]
        self.conf['watched-users'][auth]['last'] = best
        self.conf.save()
      await asyncio.sleep(30)

  async def osu_embed(self, osu_obj):
    em = Embed()
    if type(osu_obj) == osuapi.model.Beatmap:
      length = osu_obj.total_length
      length = '{:02}:{:02}:{:02}'.format(length//3600, length//60, length%60)
      em.title = osu_obj.title
      em.url   = 'https://osu.ppy.sh/b/{}'.format(osu_obj.beatmap_id)
      em.add_field(name='Artist',    value=osu_obj.artist)
      em.add_field(name='Creator',   value=osu_obj.creator)
      em.add_field(name='Difficulty',value='{:.2}'.format(i.difficultyrating))
      em.add_field(name='BPM',       value=str(osu_obj.bpm))
      em.add_field(name='Source',    value=osu_obj.source)
      em.add_field(name='Max Combo', value=str(osu_obj.max_combo))
      em.add_field(name='Length',    value=length)
    elif type(osu_obj) == list:
      if len(osu_obj) == 0:
        return None
      diff     = ', '.join(['{:.2}'.format(i.difficultyrating)for i in osu_obj])
      em       = self.osu_embed(osu_obj[0])
      em.url   = 'https://osu.ppy.sh/s/{}'.format(osu_obj[0].beatmapset_id)
      em.fields[2] = diff
      em.remove_field(3)
      em.remove_field(4)
      return em
    elif type(osu_obj) == osuapi.model.User:
      rank  = '#{0.pp_rank} ({0.country} #{0.pp_country_rank})'.format(osu_obj)
      level = int(osu_obj.level)
      nextl = osu_obj.level * 100 % 100

      em.title = osu_obj.username
      em.url   = 'https://osu.ppy.sh/u/{}'.format(osu_obj.user_id)
      em.add_field(name='Rank',      value=rank)
      em.add_field(name='Accuracy',  value='{:02.4}%'.format(osu_obj.accuracy))
      em.add_field(name='Level',     value='{} ({:02.4}%)'.format(level, nextl))
      em.add_field(name='Total PP',  value=str(osu_obj.pp_raw))
      em.add_field(name='Play Count',value=str(osu_obj.playcount))
    em.set_image(url=get_thumb_url(osu_obj))
    return em

def get_thumb_url(osu_obj):
  if type(osu_obj) == osuapi.model.Beatmap:
    return 'https://b.ppy.sh/thumb/{}l.jpg'.format(osu_obj.beatmap_id)
  elif type(osu_obj) == osuapi.model.User:
    return 'https://a.ppy.sh/{}.png'.format(osu_obj.user_id)
  return 'http://w.ppy.sh/c/c9/Logo.png'

def setup(bot):
  o = Osu(bot)
  bot.add_listener(o.osu_info, "on_message")
  bot.add_cog(o)
