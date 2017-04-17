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
  try:
    discord.opus.load_opus('opus')
  except:
    discord.opus.load_opus(find_library('opus'))

class VoiceEntry:
  def __init__(self, item, player):
    self.item   = item
    self.player = player

class VoiceState:
  def __init__(self, bot):
    self.vchan          = None
    self.current        = None
    self.bot            = bot
    self.play_next_song = asyncio.Event()
    self.songs          = asyncio.Queue()
    self.audio_player   = self.bot.loop.create_task(self.audio_player_loop())

  def is_playing(self):
    if self.vchan is None or self.current is None:
      return False

    player = self.current.player
    return not player.is_done()

  @property
  def player(self):
    return self.current.player

  def skip(self):
    if self.is_playing():
      self.player.stop()

  def toggle_next(self):
    self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

  async def audio_player_loop(self):
    while True:
      self.play_next_song.clear()
      self.current = await self.songs.get()
      em = await makeEmbed(self.current.item, 'Now playing: ')
      await self.bot.send_message(self.current.channel, embed=em)
      self.current.player.start()
      await self.play_next_song.wait()

class Player:
  def __init__(self, bot):
    self.voice_states = {}
    self.bot          = bot

  def get_voice_state(self, server):
    state = self.voice_states.get(server.id)
    if state is None:
      state = VoiceState(self.bot)
      self.voice_states[server.id] = state
    return state

  async def create_voice_client(self, channel):
    vchan = await self.bot.join_voice_channel(channel)
    state = self.get_voice_state(channel.server)
    state.vchan = vchan

  def unload(self):
    for state in self.voice_states.values():
      try:
        state.audio_player.cancel()
        if state.vchan:
          self.bot.loop.create_task(state.vchan.disconnect())
      except:
        pass

  async def join(self, ctx, channel : discord.Channel):
    """Joins a voice channel."""
    try:
      await self.create_voice_client(channel)
    except discord.ClientException:
      await self.bot.say('Already in a voice channel.')
    except discord.InvalidArgument:
      await self.bot.say('That\'s not a voice channe;.')
    else:
      await self.bot.say('Joined ' + channel.name)

  async def summon(self, ctx):
    """Summons the bot to join your voice channel."""
    summoned_channel = ctx.message.author.voice_channel
    if summoned_channel is None:
      await self.bot.say('You are not in a voice channel.')
      return False

    state = self.get_voice_state(ctx.message.server)
    if state.vchan is None:
      state.vchan = await self.bot.join_voice_channel(summoned_channel)
    else:
      await state.vchan.move_to(summoned_channel)

    return True

  async def play(self, ctx, song : str):
    state = self.get_voice_state(ctx.message.server)
    item  = None

    success = await ctx.invoke(self.summon)
    if not success:
      return

    try:
      item = await loop.run_in_executor(None, self.conn.info, song)
    except:
      try:
        item = await loop.run_in_executor(None, self.conn.search, song)
        item = [i for i in item if i.media_type == 'Audio'][0]
      except:
        self.bot.say('could not find song')
    print(item.stream_url)
    stream = requests.get(item.stream_url, stream=True, validate=False).raw
    player = await state.vchan.create_stream_player(stream,
                                                    after=state.toggle_next
    )
    player.volume = 0.5
    entry = VoiceEntry(ctx.message, player)
    em = await makeEmbed(itme, 'Queued: ')
    await self.bot.say(embed=em)
    await state.songs.put(entry)

  async def volume(self, server, value : int):
    state = self.get_voice_state(server)
    if state.is_playing():
      player = state.player
      player.volume = value / 100
      self.bot.say('Set the volume to {:.0%}'.format(player.volume))

  async def pause(self, ctx):
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.pause()

  async def resume(self, ctx):
    """Resumes the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.resume()

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

  async def skip(self, ctx):
    state = self.get_voice_state(ctx.message.server)
    if not state.is_playing():
      await self.bot.say('Not playing anything.')
      return
    state.skip()

  async def playing(self, ctx):
    """Shows info about the currently played song."""

    state = self.get_voice_state(ctx.message.server)
    if state.current is None:
      await self.bot.say('Not playing anything.')
    else:
      em = await makeEmbed(state.current.item, 'Now Playing: ')
      await self.bot.say(embed = em)

async def makeEmbed(item, message=''):
  loop = asyncio.get_event_loop()
  em = Embed()
  img_url          = item.primary_image_url
  if 'https' in img_url:
    img_url        = await loop.run_in_executor(None, puush.get_url, img_url)
  em.title         = message + item.name
  try:
    em.description = item.overview
  except:
    em.description = item.media_type
  em.url           = item.url
  em.colour        = getColour(item.id)
  em.set_thumbnail(url=img_url)
  return em
