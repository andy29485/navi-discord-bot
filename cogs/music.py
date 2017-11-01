#!/usr/bin/env python3

import asyncio
import discord
import mutagen
import random
import re
import os
import logging
from discord.ext import commands
from ctypes.util import find_library
from cogs.utils.format import *
from cogs.utils.config import Config
import cogs.utils.emby_helper as emby_helper
import cogs.utils.discord_helper as dh

logger = logging.getLogger('navi.music')

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

    function = lambda chan: chan.type == discord.ChannelType.text
    mchan = dh.get_channel(message.server, 'music', function)
    bchan = dh.get_channel(message.server, 'bot', function)

    self.channel = mchan or bchan or self.channel

  def __str__(self):
    fmt = '*{0.title}* by {0.uploader} and requested by {1.display_name}'
    duration = self.player.duration
    if duration:
      fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
    return fmt.format(self.player, self.requester)


class VoiceState:
  def __init__(self, bot, cog, sid):
    self.current = None
    self.vchan   = None
    self.sid = sid
    self.bot = bot
    self.cog = cog
    self.play_next_song = asyncio.Event()
    self.songs          = asyncio.Queue()
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

  async def stop(self):
    if self.is_playing():
      self.player.stop()

    try:
      self.audio_player.cancel()
      await self.vchan.disconnect()
      del self.cog.voice_states[self.sid]
    except:
      pass

  async def emby_player(self, item):
    if os.path.exists(item.path):
      try:
        if not item.overview:
          f = mutagen.File(item.path)
          comment = ' '.join(f.get('comment', []))
          if comment:
            item.overview = comment
            item.post()
      except:
        pass
      url  = item.path
    else:
      url  = item.stream_url
    player = self.vchan.create_ffmpeg_player(url,
                                  before_options=' -threads 4 ',
                                  options='-b:a 64k -threads 2 -bufsize 64k',
                                  after=self.toggle_next
    )
    player.duration   = int(float(item.object_dict['RunTimeTicks']) * (10**-7))
    player.title      = item.name
    try:
      player.uploader = ', '.join(item.artist_names)
    except:
      player.uploader = '-'
    player.volume     = self.cog.conf.get('volume', {}).get(item.id, 60) / 100

    return player

  async def audio_player_task(self):
    while self.cog == self.bot.get_cog('Music'):
      self.play_next_song.clear()
      self.skip_votes.clear()

      handle = self.bot.loop.call_later(300,
                  lambda: asyncio.ensure_future(self.stop())
      )
      logger.debug('waiting for music')
      self.current = await self.songs.get()
      logger.debug('song get')
      try:
        logger.debug('music 1')
        handle.cancel()
        logger.debug('music 2')
      except:
        logger.exception('Error while attempting to start music')
        pass

      logger.debug('music 3')
      if self.current.item:
        logger.debug('music 4')
        em = await emby_helper.makeEmbed(self.current.item, 'Now playing: ')
        logger.debug('sending music np to %s - %s', self.current.channel,
                                                    str(em.to_dict())
        )
        await self.bot.send_message(self.current.channel, embed=em)
      else:
        logger.debug('music 5')
        await self.bot.send_message(self.current.channel,
          'Now playing: ' + str(self.current)
        )

      logger.debug('music 6')
      if not self.player:
        logger.debug('music 7')
        self.current.player = await self.emby_player(self.current.item)

      logger.debug('music 8')
      self.player.start()

      logger.debug('music 9')
      if hasattr(self.player, 'process'):
        logger.debug('music 10')
        await asyncio.sleep(3)

        for i in range(10):
          logger.debug('music 11')
          if self.play_next_song.is_set():
            logger.debug('music 12')
            break
          elif self.player.process.poll():
            logger.debug('music 13')
            self.current.player = await self.emby_player(self.current.item)
            self.player.start()
          elif self.player.process.poll() is None:
            logger.debug('music 14')
            await asyncio.sleep(1)
          else:
            logger.debug('music 15')
            break

      logger.debug('music 16')
      await self.play_next_song.wait()

class Music:
  def __init__(self, bot):
    self.bot = bot
    self.voice_states = {}
    self.conn = emby_helper.conn
    self.conf = Config('configs/music.json')
    if 'volume' not in self.conf:
      self.conf['volume'] = {}

    self.bot.loop.create_task(self.update_db())

  async def update_db(self):
    while self == self.bot.get_cog('Music'):
      for item in ('playlists', 'songs', 'albums', 'artists'):
        prop = lambda: getattr(self.conn, item+'_force')
        await self.bot.loop.run_in_executor(None, prop)
      await asyncio.sleep(120)

  @commands.group(pass_context=True, aliases=['m'])
  async def music(self, ctx):
    """Manage music player stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(error("Please specify valid subcommand"))

  @music.command(pass_context=True, aliases=['u', 'reload'])
  async def update(self, ctx):
    '''reload database from emby'''
    for item in ('playlists', 'songs', 'albums', 'artists'):
      prop = lambda: getattr(self.conn, item+'_force')
      await self.bot.loop.run_in_executor(None, prop)
    await self.bot.say(ok('database reloaded '))

  def get_voice_state(self, server):
    state = self.voice_states.get(server.id)
    if state is None:
      state = VoiceState(self.bot, self, server.id)
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

  @music.command(pass_context=True, no_pm=True)
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

  @music.command(pass_context=True, no_pm=True)
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

  @music.command(pass_context=True, aliases=['p'], no_pm=True)
  async def play(self, ctx, *, search : str):
    """Plays a searched song from emby.

    usage: .play [-rsam] [<number>] <search terms...>

    flags:
      -n will insert the songs next into the queue(not at the end)
      -r and -s will shuffle the songs
      -n will queue next instead of queue last
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
    qnext  = False
    mult   = False
    shuf   = False
    num    = 0

    while search:
      if re.search('^\\d{1,2}$', search[0]):
        mult  = True
        num   = int(search[0])
        search = search[1:]
      elif search[0] == '-':
        search = search[1:]
      elif search[0][0] == '-':
        for flag in search[0][1:]:
          if flag in 'am':
            search = search[1:]
            mult   = True
          elif flag in 'rs':
            search = search[1:]
            shuf   = True
          elif flag in 'n':
            search = search[1:]
            qnext  = True
          else:
            break
        else:
          continue
        break
      else:
        break
    state = self.get_voice_state(ctx.message.server)

    if state.vchan is None:
      success = await ctx.invoke(self.summon)
      if not success:
        await self.bot.say("error joining channel")
        return

    try:
      run = [
        lambda:self.conn.playlists,
        lambda:self.conn.songs,
        lambda:self.conn.albums,
        lambda:self.conn.artists
      ]

      plsts = await self.bot.loop.run_in_executor(None, run[0])
      songs = await self.bot.loop.run_in_executor(None, run[1])
      albms = await self.bot.loop.run_in_executor(None, run[2])
      artts = await self.bot.loop.run_in_executor(None, run[3])

      items = await self.bot.loop.run_in_executor(None, search_f, search,
                                                 *plsts, *albms, *artts, *songs
      )

      if not items:
        await self.bot.say('could not find song')
        return

      if hasattr(items[0], 'songs') and items[0].songs:
        display_item = items[0]
        items        = items[0].songs
      else:
        display_item = self.conn

      items = [s for s in items if s.type == 'Audio']

      if not items:
        await self.bot.say('could not find song')
        return

      if shuf:
        random.shuffle(items)

      if mult:
        if num > 0:
          items = items[:num]
        em = await emby_helper.makeEmbed(display_item, 'Queued: ')
        songs_str = ''
        for i in items:
          if hasattr(i, 'index_number'):
            songs_str += f'{i.index_number:02} - {i.name}\n'
          else:
            songs_str += f'{i.name}\n'
          await self._play_emby(ctx, state, i, display=False, qnext=qnext)
        if qnext:
          songs_str = songs_str.split('\n')
          songs_str = '\n'.join(songs_str[::-1])
        if len(songs_str) >= 1024:
          songs_str = songs_str[:1020]+'\n...'
        em.add_field(name='Items', value=songs_str)
        await self.bot.say(embed=em)
      else:
        await self._play_emby(ctx, state, random.choice(items), qnext=qnext)

    except Exception as e:
      fmt='An error occurred while processing this request: ```py\n{}: {}\n```'
      await self.bot.send_message(ctx.message.channel,
                                  fmt.format(type(e).__name__, e)
      )
      raise

  async def _play_emby(self, ctx, state, item, display=True, qnext=False):
    entry = VoiceEntry(ctx.message, item=item)
    if display:
      em = await emby_helper.makeEmbed(item, 'Queued: ')
      await self.bot.say(embed=em)
    if qnext:
      state.songs._queue.appendleft(entry)
      state.songs._unfinished_tasks += 1
      state.songs._finished.clear()
      state.songs._wakeup_next(state.songs._getters)
    else:
      await state.songs.put(entry)

  @music.command(pass_context=True, aliases=['t'], no_pm=True)
  async def tag(self, ctx, *tags):
    '''
    Tag the currently playing song

    currently avalible: instrumental drama
    eg. .music tag i
    '''
    state = self.get_voice_state(ctx.message.server)

    if not state.is_playing():
      await self.bot.say(error("Not playing anything, can't tag"))
      return
    if not state.current.item:
      await self.bot.say(error("Not an emby item, can't tag"))
      return

    item   = state.current.item
    path   = item.path
    muten  = mutagen.File(item.path)
    genres = muten.get('genre', [])
    bpost  = False
    bname  = False

    for t in tags:
      t = t.lower()
      if t in ('i', 'instrumental'):
        if 'instrumental' not in path:
          path  = path.rpartition('.')
          path  = f'{path[0]} -instrumental-.{path[2]}'
          bname = True
      elif t in ('d', 'drama'):
        if 'drama' not in ' '.join(genres).lower():
          genres.append('Drama')
          muten['genre'] = '; '.join(genres)
          item.genres    = genres
          bpost = True

    if bpost:
      item.post()
      muten.save()
    if bname:
      os.rename(item.path, path)
    await self.bot.say(ok('tags set'))

  @music.command(pass_context=True, aliases=['shuff'], no_pm=True)
  async def shuffle(self, ctx):
    """Shuffles the queue (excluding the current song)"""

    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      random.shuffle(state.songs._queue)
      await self.bot.say(ok('items shuffled'))
    else:
      await self.bot.say(error('nothing seems to be playing'))

  @music.command(pass_context=True, aliases=['v'], no_pm=True)
  async def volume(self, ctx, value : int):
    """Sets the volume of the currently playing song."""

    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.volume = value / 100
      if state.current.item:
        if value == 60 and state.current.item.id in self.conf['volume']:
          del self.conf['volume'][state.current.item.id]
        elif value != 60:
          self.conf['volume'][state.current.item.id] = value
        self.conf.save()
      await self.bot.say(f'Set the volume to {player.volume:.0%}')
    else:
      await self.bot.say(error('Nothing seems to be playing'))

  @music.command(pass_context=True, no_pm=True)
  async def pause(self, ctx):
    """Pauses the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.pause()

  @music.command(pass_context=True, aliases=['q'], no_pm=True)
  async def queue(self, ctx):
    """Checks the song queue, up to 30."""
    state = self.get_voice_state(ctx.message.server)

    if not state.is_playing():
      await self.bot.say("It seems as though nothing is playing")
      return

    songs = state.songs._queue
    em = await emby_helper.makeEmbed(self.conn, 'Queued: ')
    songs_str = ''
    for index,song in zip(range(1,31),songs):
      item = getattr(song, 'item', None)
      if item:
        songs_str += f'{index:02} - {item.name}\n'
      else:
        songs_str += f'{index:02} - {song}\n'
    em.add_field(name='Items', value=songs_str)
    await self.bot.say(embed=em)

  @music.command(pass_context=True, no_pm=True)
  async def resume(self, ctx):
    """Resumes the currently played song."""
    state = self.get_voice_state(ctx.message.server)
    if state.is_playing():
      player = state.player
      player.resume()

  @music.command(pass_context=True, aliases=['s'], no_pm=True)
  async def stop(self, ctx):
    """Stops playing audio and leaves the voice channel.

    This also clears the queue.
    """
    server = ctx.message.server
    state  = self.get_voice_state(server)

    await state.stop()

  @music.command(pass_context=True, no_pm=True)
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
    elif voter.id not in (m.id for m in state.vchan.voice_members):
      await self.bot.say(error("You're not even in the voice channel. No."))
    elif voter.id not in state.skip_votes:
      state.skip_votes.add(voter.id)
      total_votes = len(state.skip_votes)
      if total_votes >= 3:
        await self.bot.say('Skip vote passed, skipping song...')
        state.skip()
      else:
        await self.bot.say(f'Skip vote added, currently at [{total_votes}/3]')
    else:
      await self.bot.say('You have already voted to skip this song.')

  @music.command(pass_context=True, aliases=['np'], no_pm=True)
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
        string = str(state.current)
        await self.bot.say(f'Now playing {string} [skips: {skip_count}/3]')

  @music.group(pass_context=True, name='playlist', aliases=['list'], no_pm=True)
  async def _playlist(self, ctx):
    '''Manage emby playlists'''
    if ctx.invoked_subcommand is None:
      await self.bot.say(error("Please specify valid subcommand"))

  @_playlist.command(pass_context=True, name='add',
                     aliases=['n', 'new', 'add_songs', 'a'], no_pm=True)
  async def _playlist_new(self, ctx, options : str):
    '''
    create a new playlist - or adds songs to existing playlist

    Usage: .music playlist add <name of playlist>
            <song1 search criteria>
            <song2 search criteria>
            ...

    Creates a playlist with the name specifed if it does not exist,
      if more lines are provided, the first song matching the creteria
      provided by that line will be added to the playlist
      (creteria works like `.music play <search>`)
    '''
    options = options.split('\n')
    items   = []

    plsts = await self.bot.loop.run_in_executor(None,lambda:self.conn.playlists)
    songs = await self.bot.loop.run_in_executor(None,lambda:self.conn.songs)
    albms = await self.bot.loop.run_in_executor(None,lambda:self.conn.albums)
    artts = await self.bot.loop.run_in_executor(None,lambda:self.conn.artists)

    run      = lambda: search_f(options[0].split(), *plsts)
    found    = await self.bot.loop.run_in_executor(None, run)
    playlist = found[0] if found else None

    for search in options[1:]:
      run   = lambda: search_f(search.split(), *songs, *albms, *artts)
      found = await self.bot.loop.run_in_executor(None, run)
      if found:
        items.append(found[0])

    if playlist:
      run = lambda: playlist.add_items(*items)
      msg = 'Songs added'
    else:
      run = lambda: self.conn.create_playlist(name, *items)
      msg = 'Playlist created'
    await self.bot.loop.run_in_executor(None, run)
    await self.bot.say(ok(msg))

  @_playlist.command(pass_context=True, name='remove_songs',
                     aliases=['rm', 'rs', 'rm_songs', 'r'], no_pm=True)
  async def _playlist_rm_songs(self, ctx, options : str):
    '''
    remove songs from an existing playlist

    Usage: .music playlist remove_songs <name of playlist>
            <song1 search criteria>
            <song2 search criteria>
            ...

    First line is the search criteria for the playlist, following lines are
      per song search criteria. If a song is not in the playlist or the search
      does not match any song - that line will be ignored
    '''
    options = options.split('\n')
    items   = []

    plsts = await self.bot.loop.run_in_executor(None,lambda:self.conn.playlists)

    run      = lambda: search_f(options[0].split(), *plsts)
    found    = await self.bot.loop.run_in_executor(None, run)
    playlist = found[0] if found else None

    if not playlist:
      await self.bot.say(error('could not find playlist'))
      return

    songs = await self.bot.loop.run_in_executor(None,lambda:self.conn.songs)
    albms = await self.bot.loop.run_in_executor(None,lambda:self.conn.albums)
    artts = await self.bot.loop.run_in_executor(None,lambda:self.conn.artists)

    for search in options[1:]:
      run   = lambda: search_f(search.split(), *playlist.items)
      found = await self.bot.loop.run_in_executor(None, run)
      if found:
        items.append(found[0])

    run = lambda: playlist.add_items(*items)
    await self.bot.loop.run_in_executor(None, run)
    await self.bot.say(ok('Songs removed'))

  @_playlist.command(pass_context=True, name='list', aliases=['ls', 'l'])
  async def _playlist_list(self, ctx, name = ''):
    '''
    list songs in specified playlist

    if no playlist is specified, list all playlists
    '''
    run = lambda: self.conn.playlists
    playlists = await self.bot.loop.run_in_executor(None, run)

    if not name:
      names = ''
      for playlist in playlists:
        names += f'{playlist.id} - {playlist.name}\n'
      await self.bot.say(code(names))
      return

    run   = lambda: search_f(name.split(), *playlists)
    found = await self.bot.loop.run_in_executor(None, run)

    if not found:
      await self.bot.say(error("Could not find playlist"))
      return

    playlist = found[0]
    songs = await self.bot.loop.run_in_executor(None,lambda:playlist.songs)
    song_info = ''
    for song in songs:
      song_info += f'{song.id} - {song.name} ({song.album_artist_name})\n'
    await self.bot.say(code(song_info))
    return


def search_f(terms, *items):
  out   = []
  terms = set(terms)
  for item in items:
    strings = [item.id, item.name]
    for attr in ('artist_names', 'overview', 'path'):
      if hasattr(item, attr):
        attribute = getattr(item, attr, '')
        if type(attribute) == list:
          attribute = ', '.join(attribute)
        if attribute:
          strings.append(attribute)
    if match(terms, *strings):
      out.append(item)
  return out

def match(pattern, *strings):
  for patt in pattern:
    lowered = patt.lower()
    if strings[0].lower() == patt: # ID matched
      return True
    nonNegative = False
    for string in strings[1:]:
      if lowered[0] == '-':
        if lowered[1:] in string.lower():
          return False
      elif lowered in string.lower():
        break
      else:
        nonNegative = True
    else:
      if nonNegative:
        return False
  return True

def setup(bot):
  bot.add_cog(Music(bot))
