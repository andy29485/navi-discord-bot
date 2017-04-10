#!/usr/bin/env python3

from discord.ext import commands
from cogs.utils.config import Config
from cogs.utils.format import *
from discord import Embed
import discord
import asyncio
import requests
import hashlib
import logging
from embypy import Emby as EmbyPy
from embypy.objects import EmbyObject
import re
from cogs.utils import puush

colours = [0x1f8b4c, 0xc27c0e, 0x3498db, 0x206694, 0x9b59b6,
           0x71368a, 0xe91e63, 0xe67e22, 0xf1c40f, 0x1abc9c,
           0x2ecc71, 0xa84300, 0xe74c3c, 0xad1457, 0x11806a]

if not discord.opus.is_loaded():
  discord.opus.load_opus('opus')

class VoiceEntry:
  def __init__(self, message, player):
    self.requester = message.author
    self.channel   = message.channel
    self.player    = player

  def __str__(self):
    fmt = '*{0.name}* requested by {1.display_name}'
    duration = self.player.duration
    if duration:
      fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
    return fmt.format(self.player, self.requester)

class VoiceState:
  def __init__(self, bot):
    self.current        = None
    self.voice          = None
    self.bot            = bot
    self.play_next_song = asyncio.Event()
    self.songs          = asyncio.Queue()
    self.skip_votes     = set() # a set of user_ids that voted
    self.audio_player   = self.bot.loop.create_task(self.audio_player_task())

  def is_playing(self):
    if self.voice is None or self.current is None:
      return False

    player = self.current.player
    return not player.is_done()

  @property
  def player(self):
    return self.current.player

  def skip(self):
    self.skip_votes.clear()
    if self.is_playing():
      self.player.stop()

  def toggle_next(self):
    self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

  async def audio_player_task(self):
    while True:
      self.play_next_song.clear()
      self.current = await self.songs.get()
      await self.bot.send_message(self.current.channel,
                                  'Now playing ' + str(self.current)
      )
      self.current.player.start()
      await self.play_next_song.wait()

class Emby:
  def __init__(self, bot):
    self.bot          = bot
    self.conf         = Config('configs/emby.json')
    self.voice_states = {}

    if 'address' not in self.conf or not self.conf['address']:
      self.conf['address'] = input('Enter emby url: ')
      self.conf.save()
    if 'auth' not in self.conf or not self.conf['auth']:
      self.conf['auth'] = {}
      self.conf['auth']['api_key']   = input('Enter emby api key: ')
      self.conf['auth']['userid']    = input('Enter emby user id: ')
      self.conf['auth']['device_id'] = input('Enter emby device id: ')
      self.conf.save()

    self.conn = EmbyPy(self.conf['address'], **self.conf['auth'], ws=True)
    self.conn.connector.set_on_message(self.on_socket_message)

  @commands.group(pass_context=True)
  async def emby(self, ctx):
    """Manage emby stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(formatter.error("Please specify valid subcommand"))

  @emby.command(name='lookup', aliases=['info', 'i'], pass_context=True)
  async def _info(self, ctx, *, item_ids = ''):
    """print emby server info, or an embed for each item id"""
    loop = asyncio.get_event_loop()
    for item_id in item_ids.split():
      item = await loop.run_in_executor(None, self.conn.info, item_id)
      em   = await makeEmbed(item)
      await self.bot.send_message(ctx.message.channel, embed=em)
    if not item_ids:
      info = await loop.run_in_executor(None, self.conn.info)
      await self.bot.say(info)

  @emby.command(name='search', aliases=['find', 's'], pass_context=True)
  async def _search(self, ctx, *, query : str):
    """searches for query on emby, displays first result

    if first "word" in query is a number, returns that many results
    (ignoring the number)
    """

    match = re.search(r'^(\d)+\s+(\S.*)$', query)
    if not query:
      await self.bot.say(formatter.error('missing query'))
      return
    elif match:
      num   = int(match.group(1))
      query = match.group(2)
    else:
      num   = 1

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, self.conn.search, query)
    results = [i for i in results if issubclass(type(i), EmbyObject)]
    if not results:
      await self.bot.say('No results found')
      return

    types_map = {'BoxSet':0, 'Series':1, 'Movie':2, 'Audio':3, 'Person':4}
    m_size    = len(types_map)
    results   = sorted(results, key = lambda x : types_map.get(x.type, m_size))

    for result in results[:num]:
      await loop.run_in_executor(None, result.update)
      em = await makeEmbed(result)
      await self.bot.send_message(ctx.message.channel, embed=em)

  def get_voice_state(self, server):
    state = self.voice_states.get(server.id)
    if state is None:
      state = VoiceState(self.bot)
      self.voice_states[server.id] = state
    return state

  async def create_voice_client(self, channel):
    voice = await self.bot.join_voice_channel(channel)
    state = self.get_voice_state(channel.server)
    state.voice = voice

  def __unload(self):
    for state in self.voice_states.values():
      try:
        state.audio_player.cancel()
        if state.voice:
          self.bot.loop.create_task(state.voice.disconnect())
      except:
        pass

  @emby.command(pass_context=True, no_pm=True)
  async def join(self, ctx, *, channel : discord.Channel):
    """Joins a voice channel."""
    try:
      await self.create_voice_client(channel)
    except discord.ClientException:
      await self.bot.say('Already in a voice channel.')
    except discord.InvalidArgument:
      await self.bot.say('That\'s not a voice channe;.')
    else:
      await self.bot.say('Joined ' + channel.name)

  @emby.command(pass_context=True, no_pm=True)
  async def summon(self, ctx):
    """Summons the bot to join your voice channel."""
    summoned_channel = ctx.message.author.voice_channel
    if summoned_channel is None:
      await self.bot.say('You are not in a voice channel.')
      return False

    state = self.get_voice_state(ctx.message.server)
    if state.voice is None:
      state.voice = await self.bot.join_voice_channel(summoned_channel)
    else:
      await state.voice.move_to(summoned_channel)

    return True

  @emby.command(pass_context=True, no_pm=True)
  async def play(self, ctx, *, song : str):
    """Plays a song.
    If there is a song currently in the queue, then it is
    queued until the next song is done playing.
    This command automatically searches as well from YouTube.
    The list of supported sites can be found here:
    https://rg3.github.io/youtube-dl/supportedsites.html
    """
    state = self.get_voice_state(ctx.message.server)
    opts = {
      'default_search': 'auto',
      'quiet': True,
    }

    if state.voice is None:
      success = await ctx.invoke(self.summon)
      if not success:
        return

    try:
      item = await loop.run_in_executor(None, self.conn.search, song)
      item = [i for i in item if i.media_type == 'Audio'][0]
    except:
      self.bot.say('could not find song')
    stream = requests.get(item.stream_url, stream=True, validate=False).raw

    player = await state.voice.create_stream_player(stream,
                                                    after=state.toggle_next
    )
    player.volume = 0.5
    entry = VoiceEntry(ctx.message, player)
    await self.bot.say('Queued ' + str(entry))
    await state.songs.put(entry)

  @emby.command(pass_context=True, no_pm=True)
  async def volume(self, ctx, value : int):
    """Sets the volume of the currently playing song."""

    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.volume = value / 100
      await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

  @emby.command(pass_context=True, no_pm=True)
  async def pause(self, ctx):
    """Pauses the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.pause()

  @emby.command(pass_context=True, no_pm=True)
  async def resume(self, ctx):
    """Resumes the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.resume()

  @emby.command(pass_context=True, no_pm=True)
  async def stop(self, ctx):
    """Stops playing audio and leaves the voice channel.
    This also clears the queue.
    """
    server = ctx.message.server
    state = self.get_voice_state(server)

    if state.is_playing():
      player = state.player
      player.stop()

    try:
      state.audio_player.cancel()
      del self.voice_states[server.id]
      await state.voice.disconnect()
    except:
      pass

  @emby.command(pass_context=True, no_pm=True)
  async def skip(self, ctx):
    """Retweet to skip a song. The song requester can automatically skip.
    3 skip likes on facebook are needed for the song to be skipped.
    """

    state = self.get_voice_state(ctx.message.server)
    if not state.is_playing():
      await self.bot.say('Not playing any music right now...')
      return

    voter = ctx.message.author
    if voter == state.current.requester:
      await self.bot.say('Requester requested skipping song...')
      state.skip()
    elif voter.id not in state.skip_votes:
      state.skip_votes.add(voter.id)
      total_votes = len(state.skip_votes)
      if total_votes >= 3:
        await self.bot.say('Skip retweet passed, skipping song...')
        state.skip()
      else:
        await self.bot.say('Skip retweet added, currently at [{}/3]'.format(total_votes))
    else:
      await self.bot.say('You have already voted to skip this song.')

  @emby.command(pass_context=True, no_pm=True)
  async def playing(self, ctx):
    """Shows info about the currently played song."""

    state = self.get_voice_state(ctx.message.server)
    if state.current is None:
      await self.bot.say('Not playing anything.')
    else:
      skip_count = len(state.skip_votes)
      await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))


  async def on_socket_message(self, message):
    if message['MessageType'] == 'LibraryChanged':
      for eid in message['ItemsAdded']:
        logging.info(eid+' has been added to emby')
        print(eid+' has been added to emby')

async def makeEmbed(item):
  loop = asyncio.get_event_loop()
  em = Embed()
  img_url          = item.primary_image_url
  if 'https' in img_url:
    img_url        = await loop.run_in_executor(None, puush.get_url, img_url)
  em.title         = item.name
  try:
    em.description = item.overview
  except:
    em.description = item.media_type
  em.url           = item.url
  em.colour        = getColour(item.id)
  em.set_thumbnail(url=img_url)
  return em

def getColour(string : str):
  str_hash = hashlib.md5()
  str_hash.update(string.strip().encode())
  str_hash = int(str_hash.hexdigest(), 16)
  return colours[str_hash % len(colours)]

def setup(bot):
  bot.add_cog(Emby(bot))
