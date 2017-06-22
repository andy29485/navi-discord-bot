#!/usr/bin/env python3

import asyncio
import discord
import random
import re
from discord.ext import commands
from ctypes.util import find_library
import cogs.utils.emby_helper as emby_helper
from cogs.utils.format import *

if not discord.opus.is_loaded():
  try:
    discord.opus.load_opus('opus')
  except:
    discord.opus.load_opus(find_library('opus'))

class VoiceEntry:
  def __init__(self, message, player=None, item=None):
    self.requester = message.author
    self.channel   = message.channel
    self.player    = player
    self.item      = item

  def __str__(self):
    fmt = '*{0.title}* by {0.uploader} and requested by {1.display_name}'
    duration = self.player.duration
    if duration:
      fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
    return fmt.format(self.player, self.requester)


class VoiceState:
  def __init__(self, bot, cog):
    self.current = None
    self.vchan = None
    self.bot = bot
    self.cog = cog
    self.play_next_song = asyncio.Event()
    self.songs = asyncio.Queue()
    self.skip_votes = set() # a set of user_ids that voted
    self.audio_player = self.bot.loop.create_task(self.audio_player_task())

  def is_playing(self):
    if self.vchan is None or self.current is None:
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

  async def emby_player(self, item):
    url    = item.stream_url
    player = self.vchan.create_ffmpeg_player(url,
                                              before_options=' -threads 4 ',
                                              options='-b:a 64k -bufsize 64k',
                                              after=self.toggle_next
    )
    player.duration = int(float(item.object_dict['RunTimeTicks']) * (10**-7))
    player.title    = item.name
    player.uploader = ', '.join(item.artist_names)
    player.volume   = 0.6

    return player

  async def audio_player_task(self):
    while self.cog == self.bot.get_cog('Music'):
      self.play_next_song.clear()
      self.current = await self.songs.get()
      if self.current.item:
        em = await emby_helper.makeEmbed(self.current.item, 'Now playing: ')
        await self.bot.send_message(self.current.channel, embed=em)
      else:
        await self.bot.send_message(self.current.channel,
          'Now playing: ' + str(self.current)
        )
      if not self.player:
        self.current.player = await self.emby_player(self.current.item)
      self.player.start()
      await asyncio.sleep(10)
      if hasattr(self.player, 'process') and \
         self.player.process.poll():
        self.current.player = awaitself.emby_player(item)
        self.player.start()
        await self.play_next_song.wait()
      else:
        await self.play_next_song.wait()


class Music:
  def __init__(self, bot):
    self.bot = bot
    self.voice_states = {}
    self.conn = emby_helper.conn

  def get_voice_state(self, server):
    state = self.voice_states.get(server.id)
    if state is None:
      state = VoiceState(self.bot, self)
      self.voice_states[server.id] = state

    return state

  async def create_voice_client(self, channel):
    voice = await self.bot.join_voice_channel(channel)
    state = self.get_voice_state(channel.server)
    state.vchan = voice

  def __unload(self):
    for state in self.voice_states.values():
      try:
        state.audio_player.cancel()
        if state.vchan:
          self.bot.loop.create_task(state.vchan.disconnect())
      except:
        pass

  @commands.command(pass_context=True, no_pm=True)
  async def join(self, ctx, *, channel : discord.Channel):
    """Joins a voice channel."""
    try:
      await self.create_voice_client(channel)
    except discord.ClientException:
      await self.bot.say('Already in a voice channel...')
    except discord.InvalidArgument:
      await self.bot.say('This is not a voice channel...')
    else:
      await self.bot.say('Ready to play audio in ' + channel.name)

  @commands.command(pass_context=True, no_pm=True)
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

  @commands.command(pass_context=True, no_pm=True)
  async def play(self, ctx, *, song : str):
    """Plays a song.

    If there is a song currently in the queue, then it is
    queued until the next song is done playing.

    This command searchs emby for a song
    """
    split = song.split(' ')
    mult = False
    shuf = False
    num  = 0

    while len(split) > 1:
      if split[0] == '-a' or split[0] == '-m':
        split = split[1:]
        mult  = True
      elif split[0] == '-s':
        split = split[1:]
        shuf  = True
      elif re.searchh('^\d+$', split[0]):
        split = split[1:]
        multi = True
        num   = int(split(0))
      else:
        break
    song = ' '.join(split)

    state = self.get_voice_state(ctx.message.server)
    opts = {
        'default_search': 'auto',
        'quiet': True,
    }

    if state.vchan is None:
      success = await ctx.invoke(self.summon)
      if not success:
        return

    try:
      try:
        item = await self.bot.loop.run_in_executor(None, self.conn.info, song)
      except:
        try:
          items = await self.bot.loop.run_in_executor(None,
                                                     self.conn.search,
                                                     song,
                                                     {'Playlist'    :0,
                                                      'Audio'       :1,
                                                      'MusicArtist' :2,
                                                      'MusicAlbum'  :3
                                                     },
                                                     True
          )
          item = items[0]
        except:
          await self.bot.say('could not find song')
          return
      if hasattr(item, 'songs'):
        songs = item.songs
        if shuf:
          random.shuffle(songs)
        if not songs:
          await self.bot.say('could not find song')
          return
        if mult:
          if num > 0:
            songs = songs[:num]
          em = await emby_helper.makeEmbed(item, 'Queued: ')
          songs_str = ''
          for i in songs:
            if hasattr(i, 'index_number'):
              songs_str += '{:02} - {}\n'.format(i.index_number, i.name)
            else:
              songs_str += '{}\n'.format(i.name)
            await self._play_emby(ctx, state, i, display=False)
          em.add_field(name='Items', value=songs_str)
          await self.bot.say(embed=em)
        else:
          await self._play_emby(ctx, state, random.choice(songs))
      else:
        await self._play_emby(ctx, state, item)
    except Exception as e:
      fmt='An error occurred while processing this request: ```py\n{}: {}\n```'
      await self.bot.send_message(ctx.message.channel,
                                  fmt.format(type(e).__name__, e)
      )
      raise

  async def _play_emby(self, ctx, state, item, display=True):
    entry = VoiceEntry(ctx.message, item=item)
    if display:
      em = await emby_helper.makeEmbed(item, 'Queued: ')
      await self.bot.say(embed=em)
    await state.songs.put(entry)

  @commands.command(pass_context=True, no_pm=True)
  async def volume(self, ctx, value : int):
    """Sets the volume of the currently playing song."""

    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.volume = value / 100
      await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

  @commands.command(pass_context=True, no_pm=True)
  async def pause(self, ctx):
    """Pauses the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.pause()

  @commands.command(pass_context=True, no_pm=True)
  async def resume(self, ctx):
    """Resumes the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.resume()

  @commands.command(pass_context=True, no_pm=True)
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
      await state.vchan.disconnect()
    except:
      pass

  @commands.command(pass_context=True, no_pm=True)
  async def skip(self, ctx):
    """Vote to skip a song. The song requester can automatically skip.

    3 skip votes are needed for the song to be skipped.
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
        await self.bot.say('Skip vote passed, skipping song...')
        state.skip()
      else:
        await self.bot.say('Skip vote added, currently at [{}/3]'.format(
                            total_votes
        ))
    else:
      await self.bot.say('You have already voted to skip this song.')

  @commands.command(pass_context=True, no_pm=True)
  async def playing(self, ctx):
    """Shows info about the currently played song."""

    state = self.get_voice_state(ctx.message.server)
    if state.current is None:
      await self.bot.say('Not playing anything.')
    else:
      skip_count = len(state.skip_votes)
      if state.current.item:
        em = await emby_helper.makeEmbed(state.current.item, 'Now playing: ')
        em.add_field(name="**Skip Count**", value=str(skip_count))
        await self.bot.say(embed=em)
      else:
        await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current,
                                                                 skip_count)
        )


def setup(bot):
  bot.add_cog(Music(bot))
