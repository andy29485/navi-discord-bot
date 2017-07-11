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
    if self.vchan is None or self.current is None or self.player is None:
      return False

    return not self.player.is_done()

  @property
  def player(self):
    return self.current.player

  def skip(self):
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
    player.duration   = int(float(item.object_dict['RunTimeTicks']) * (10**-7))
    player.title      = item.name
    try:
      player.uploader = ', '.join(item.artist_names)
    except:
      player.uploader = '-'
    player.volume     = 0.6

    return player

  async def audio_player_task(self):
    while self.cog == self.bot.get_cog('Music'):
      self.play_next_song.clear()
      self.skip_votes.clear()

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

      if hasattr(self.player, 'process'):
        await asyncio.sleep(3)

        for i in range(10):
          if self.play_next_song.is_set():
            break
          elif self.player.process.poll():
            self.current.player = await self.emby_player(self.current.item)
            self.player.start()
          elif self.player.process.poll() is None:
            await asyncio.sleep(1)
          else:
            break

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
  async def play(self, ctx, *, search : str):
    """Plays a searched song from emby.

    usage: .play [-rsam] [<number>] <search terms...>

    flags:
      -r and -s will shuffle the songs
      -a and -m will enable playing multiple songs
        if no number is specified then all songs will be played
        if  a number is specified then that many song will play
          if at least that many songs were found

      search terms:
        - search terms are space seperated and case insensitive
        - if a term is an itemid, that item will be included
        - will search playlists, songs, albums, and album artists FOR:
          - name/title
          - filepath
          - description
          - artist/album artist names (for songs)
        NOTE: if none are specified - all songs on emby will be considered

    If there is a song currently in the queue, then it is
    queued until the next song is done playing.

    This command searchs emby for a song
    """
    search = search.split(' ')
    mult   = False
    shuf   = False
    num    = 0

    while search:
      if search[0][0] == '-':
        for flag in search[0][1:]:
          if flag in 'am':
            search = search[1:]
            mult  = True
          elif flag in 'rs':
            search = search[1:]
            shuf  = True
          else:
            break
      elif re.search('^\\d{1,2}$', search[0]):
        mult  = True
        num   = int(search[0])
        search = search[1:]
      else:
        break
    state = self.get_voice_state(ctx.message.server)

    if state.vchan is None:
      success = await ctx.invoke(self.summon)
      if not success:
        await self.bot.say("error joining channel")
        return

    try:
      plsts=await self.bot.loop.run_in_executor(None,lambda:self.conn.playlists)
      songs=await self.bot.loop.run_in_executor(None,lambda:self.conn.songs)
      albms=await self.bot.loop.run_in_executor(None,lambda:self.conn.albums)
      artts=await self.bot.loop.run_in_executor(None,lambda:self.conn.artists)

      items = await self.bot.loop.run_in_executor(None, search_f, set(search),
                                                  *plsts, *songs, *albms, *artts
      )

      if hasattr(items[0], 'songs') and items[0].songs:
        items = items[0].songs

      items = [s for s in items if s.type == 'Audio']

      if not items:
        await self.bot.say('could not find song')
        return

      if shuf:
        random.shuffle(items)

      print(1)
      if mult:
        print(2)
        if num > 0:
          print(3)
          items = items[:num]
        print(4)
        em = await emby_helper.makeEmbed(self.conn, 'Queued: ')
        print(5)
        songs_str = ''
        for i in items:
          if hasattr(i, 'index_number'):
            songs_str += '{:02} - {}\n'.format(i.index_number, i.name)
            print(6)
          else:
            songs_str += '{}\n'.format(i.name)
            print(7)
          await self._play_emby(ctx, state, i, display=False)
        print(8)
        em.add_field(name='Items', value=songs_str)
        await self.bot.say(embed=em)
        print(9)
      else:
        print(10)
        await self._play_emby(ctx, state, random.choice(items))
        print(11)

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

def search_f(terms, *items):
  out = []
  for item in items:
    strings = [item.id, item.name]
    for attr in ('artist_names', 'overview', 'path'):
      if hasattr(item, attr):
        attribute = getattr(item, attr, '')
        if type(attribute) == list:
          attribute = ', '.join(attribute)
        strings.append(attribute)
    if match(terms, *strings):
      out.append(item)
  return out

def match(pattern, *strings):
  for patt in pattern:
    lowered = patt.lower()
    if strings[0].lower() == patt: # ID matched
      return True
    for string in strings[1:]:
      if lowered[0] == '-':
        if lowered[1:] in string.lower():
          return False
      elif lowered in string.lower():
        break
    else:
      return False
  return True

def setup(bot):
  bot.add_cog(Music(bot))
