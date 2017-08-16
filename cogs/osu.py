#!/usr/bin/env python3

import re
import asyncio
import itertools
from discord.ext import commands
from discord import Embed
import osuapi
from cogs.utils import format as formatter
from cogs.utils.config import Config

class Osu:
  breatmap_sets_url_patterns=[re.compile('https?://osu.ppy.sh/s/(\\d+)')]
  breatmap_url_patterns     =[re.compile('https?://osu.ppy.sh/b/(\\d+)')]
  user_url_patterns         =[re.compile('https?://osu.ppy.sh/u/(\\d+)')]

  def __init__(self, bot):
    self.bot           = bot
    self.loop          = bot.loop
    self.conf          = Config('configs/osu.json')

    if 'api-key' not in self.conf:
      self.conf['api-key'] = input('enter osu api key: ')
    if 'watched-users' not in self.conf:
      self.conf['watched-users'] = {}
    self.conf.save()

    self.api=osuapi.OsuApi(self.conf['api-key'],connector=osuapi.AHConnector())

    self.loop.create_task(self.check_scores())

  async def osu_info(self, message):
    if message.author.bot:
      return

    chan = message.channel

    for pattern in Osu.breatmap_sets_url_patterns:
      for bid in pattern.findall(message.content):
        beatmap = await self.api.get_beatmaps(beatmapset_id=bid)
        em = await self.osu_embed(beatmap)
        if not em:
          self.bot.send_message(chan, 'could not find beatmap')
        else:
          await self.bot.send_message(chan, embed=em)
      else:
        continue
      break

    for pattern in Osu.breatmap_url_patterns:
      for bid in pattern.findall(message.content):
        beatmap = await self.api.get_beatmaps(beatmap_id=bid)
        em = await self.osu_embed(beatmap[0])
        if not em:
          self.bot.send_message(chan, 'could not find beatmap')
        else:
          await self.bot.send_message(chan, embed=em)
      else:
        continue
      break

    for pattern in Osu.user_url_patterns:
      for uid in pattern.findall(message.content):
        user = await self.api.get_user(int(uid))
        em = await self.osu_embed(user[0])
        if not em:
          self.bot.send_message(chan, 'could not find user')
        else:
          await self.bot.send_message(chan, embed=em)
      else:
        continue
      break

  @commands.group(name='osu', aliases=["o"], pass_context=True)
  async def _osu(self, ctx):
    """
    manages osu stuff
    """
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))

  @_osu.command(name='recent', aliases=['r', 'last'], pass_context=True)
  async def _recent(self, ctx, osu_username : str =''):
    """
    shows last played map for a user
    if no user is specified, shows your last played item
    """
    #TODO - shows last played map for a user
    #       if no user is specified, show linked user latest
    #        self.conf['watched-users']['<discord id>']
    #        if discord user is not linked, ask the to link using `.osu connect`
    auth = ctx.message.author.id
    if osu_username:
      user = osu_username
    elif auth in self.conf['watched-users']:
      user = self.conf['watched-users'][auth]['uid']
    else:
      await self.bot.say('No user specified, nor are you linked to an OSU user')
      return

    user = await self.api.get_user(user)
    if not user:
      await self.bot.say('Could not find user with matching name')
      return
    user = user[0]

    last = await self.api.get_user_recent(user.user_id)
    if not last:
      await self.bot.say(f'No recent play history for {user.username}')
      return

    em = await self.osu_embed(last[0])
    print(last[0].__dict__)
    print(em.to_dict())
    await self.bot.say(embed=em)


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
    if not user:
      await self.bot.say('could not find user')
      return

    top_scores = max(0, min(100, top_scores))
    name       = user[0].username
    user       = user[0].user_id
    if top_scores:
      best     = await self.api.get_user_best(user, limit=top_scores)
      best     = [(i.beatmap_id, i.score) for i in best]
    else:
      best = []

    if auth in self.conf['watched-users']:
      self.conf['watched-users'][auth]['uid'] = user
      if chan not in self.conf['watched-users'][auth]['chans']:
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
        formatter.ok(f'you are now linked to: {name}')
    )

  async def check_scores(self):
    while self == self.bot.get_cog('Osu'):
      for duid in self.conf['watched-users']:
        ouid  = self.conf['watched-users'][duid]['uid']
        num   = self.conf['watched-users'][duid]['num']
        chans = self.conf['watched-users'][duid]['chans']
        last  = self.conf['watched-users'][duid]['last']
        name  = await self.api.get_user(ouid)
        name  = name[0].username
        best  = await self.api.get_user_best(ouid, limit=num)

        for i, old, new in itertools.zip_longest(range(num), last, best):
          if new.beatmap_id != old[0] or new.score > old[1]:
            em = await self.osu_embed(new)
            em.title = f'New best #{i+1} for {name} - {em.title}'
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
        self.conf['watched-users'][duid]['last'] = best
        self.conf.save()
      await asyncio.sleep(30)

  async def osu_embed(self, osu_obj):
    em = Embed()
    print(str(type(osu_obj)))

    if type(osu_obj) == osuapi.model.Beatmap:
      length = osu_obj.total_length
      length = f'{length//3600:02}:{length//60:02}:{length%60:02}'
      diff   = f'{osu_obj.difficultyrating:.2}'

      em.title = osu_obj.title
      em.url   = f'https://osu.ppy.sh/b/{osu_obj.beatmap_id}'
      em.add_field(name='Artist',    value=osu_obj.artist)
      em.add_field(name='Creator',   value=osu_obj.creator)
      em.add_field(name='Difficulty',value=diff)
      em.add_field(name='BPM',       value=str(osu_obj.bpm))
      em.add_field(name='Source',    value=osu_obj.source)
      em.add_field(name='Max Combo', value=str(osu_obj.max_combo))
      em.add_field(name='Length',    value=length)

    elif type(osu_obj) == list:
      if len(osu_obj) == 0:
        return None
      diff     = ', '.join([f'{i.difficultyrating:.2}' for i in osu_obj])
      em       = await self.osu_embed(osu_obj[0])
      em.url   = f'https://osu.ppy.sh/s/{osu_obj[0].beatmapset_id}'
      em.set_field_at(2, name='Difficulty', value=diff)
      em.remove_field(3) # remove BPM
      em.remove_field(4) # remove Max Combo
      return em

    elif type(osu_obj) == osuapi.model.User:
      rank  = '#{0.pp_rank} ({0.country} #{0.pp_country_rank})'.format(osu_obj)
      level = int(osu_obj.level)
      nextl = osu_obj.level * 100 % 100

      em.title = osu_obj.username
      em.url   = f'https://osu.ppy.sh/u/{osu_obj.user_id}'
      em.add_field(name='Rank',      value=rank)
      em.add_field(name='Accuracy',  value=f'{osu_obj.accuracy:02.4}%')
      em.add_field(name='Level',     value=f'{level} ({nextl:02.4}%)')
      em.add_field(name='Total PP',  value=str(osu_obj.pp_raw))
      em.add_field(name='Play Count',value=str(osu_obj.playcount))

    elif type(osu_obj) in (osuapi.model.SoloScore, osuapi.model.RecentScore):
      print(1)
      beatmap = await self.api.get_beatmaps(beatmap_id=osu_obj.beatmap_id)
      beatmap = beatmap[0]
      print(type(beatmap))
      em      = await self.osu_embed(beatmap)
      print(em.to_dict())
      rank    = osu_obj.rank.replace('X', 'SS')
      if type(osu_obj) == osuapi.model.SoloScore:
        score   = f'{osu_obj.score:,} ({rank} - {osu_obj.pp}pp)'
      else:
        score   = f'{osu_obj.score:,} ({rank})'
      combo   = f'{osu_obj.maxcombo}/{beatmap.max_combo}'
      print(2)

      em.add_field(name='Score',    value=score)
      em.add_field(name='Combo',    value=combo)
      em.remove_field(5) # remove Max Combo
      print(3)

    print(4)
    print(em.to_dict())
    if not em.thumbnail.url:
      print(5)
      em.set_thumbnail(url=await self.get_thumb_url(osu_obj))
    print(6)
    print(em.to_dict())
    return em

  async def get_thumb_url(self, osu_obj):
    if type(osu_obj) == osuapi.model.Beatmap:
      if not hasattr(osu_obj, 'beatmapset_id') or not osu_obj.beatmapset_id:
        osu_obj = await self.api.get_beatmaps(beatmap_id=osu_obj.beatmap_id)
        osu_obj = osu_obj[0]
      return f'https://b.ppy.sh/thumb/{osu_obj.beatmapset_id}l.jpg'
    elif type(osu_obj) == osuapi.model.User:
      return f'https://a.ppy.sh/{osu_obj.user_id}?.png'
    return 'http://w.ppy.sh/c/c9/Logo.png'

  def __unload(self):
    self.api.close()

def setup(bot):
  o = Osu(bot)
  bot.add_listener(o.osu_info, "on_message")
  bot.add_cog(o)
