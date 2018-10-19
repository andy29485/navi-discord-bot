import asyncio
from collections import deque
import shlex
import re
import os
import logging
import inspect

from includes.utils.format import *
from includes.utils.config import Config
import includes.utils.emby_helper as emby_helper
import includes.utils.discord_helper as dh

import discord
import youtube_dl

import mutagen
from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, TIT2, COMM

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

logger = logging.getLogger('navi.music')

ytdl_format_options = {
  'format': 'bestaudio/best',
  'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
  'restrictfilenames': True,
  'noplaylist': True,
  'nocheckcertificate': True,
  'ignoreerrors': False,
  'logtostderr': False,
  'quiet': True,
  'no_warnings': True,
  'default_search': 'auto',
  'source_address': '0.0.0.0'
}

ffmpeg_options = {
  'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
  def __init__(self, source, *, data, volume=0.5):
    super().__init__(source, volume)

    self.data = data

    self.title = data.get('title')
    self.url = data.get('url')

  @classmethod
  async def from_url(cls, url, *, loop=None, stream=False):
    loop = loop or asyncio.get_event_loop()
    run  = lambda: ytdl.extract_info(url, download=not stream)
    data = await loop.run_in_executor(None, run)

    if 'entries' in data:
      # take first item from a playlist
      data = data['entries'][0]

    filename = data['url'] if stream else ytdl.prepare_filename(data)
    return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music:
  def __init__(self, bot):
    self.bot  = bot
    self.info = {} # guild_id -> {queue, np}
    self.conn = emby_helper.conn
    self.conf = Config('configs/music.json')
    if 'volume' not in self.conf:
      self.conf['volume'] = {}

    self.bot.loop.create_task(self.update_db())

  async def update_db(self):
    while self == self.bot.get_cog('Music'):
      for item in ('playlists', 'songs', 'albums', 'artists'):
        try:
          await getattr(self.conn, item+'_force')
        except:
          pass
      await asyncio.sleep(120)

  async def _search(self, search, albm=False):
    logger.debug('search - getting db')
    plsts = await self.conn.playlists
    songs = await self.conn.songs
    albms = await self.conn.albums
    artts = await self.conn.artists

    if albm:
      logger.debug('search - with album')
      return await self.bot.loop.run_in_executor(None, search_f, search,
                                                 *plsts, *albms, *artts, *songs
      )
    logger.debug('search - no album')
    return await self.bot.loop.run_in_executor(None, search_f, search,
                                               *plsts, *songs, *albms, *artts
    )

  async def next(self, vc):
    if not vc.guild:
      return

    info  = self.info[str(vc.guild)]
    queue = info['queue']

    if queue.isEmpty():
      await vc.disconnect()

    info['np'] = item = queue.pop()
    info['skip'].clear()
    nxt = lambda e: self.next(vc)

    async with info['chan'].typing():
      if type(item) == str:
        player = await YTDLSource.from_url(item, loop=vc.loop, stream=True)
        vc.play(player, after=nxt)
        info['chan'].send(f'Now Playing: {item}')
      else:
        em = await emby_helper.makeEmbed(item, 'Now playing: ')
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(item.path))
        vc.play(source, after=nxt)
        info['chan'].send(embed=em)

  @commands.group(pass_context=True, aliases=['m'])
  async def music(self, ctx):
    """Manage music player stuff"""
    if ctx.invoked_subcommand is None:
      await self.bot.say(error("Please specify valid subcommand"))

  @music.command(pass_context=True, aliases=['u', 'reload'])
  async def update(self, ctx):
    '''reload database from emby'''
    for item in ('playlists', 'songs', 'albums', 'artists'):
      await getattr(self.conn, item+'_force')

    await self.bot.say(ok('database reloaded '))

  @music.command()
  async def summon(self, ctx, *, channel: discord.VoiceChannel = None):
    """Joins specified / your voice channel"""

    if channel == None:
      channel = ctx.author.voice.channel

    if ctx.voice_client is not None:
      return await ctx.voice_client.move_to(channel)

    await channel.connect()

  @music.command(aliases=['p'])
  async def play(self, ctx, *, query : str):
    """Plays a searched song from emby or a url

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
        - search terms are space separated and case insensitive
        - if a term is an itemid, that item will be included
        - will search playlists, songs, albums, and album artists FOR:
          - name/title
          - filepath
          - description
          - artist/album artist names (for songs)
        NOTE: if none are specified - all songs on emby will be considered

    If there is a song currently in the queue, then it is
    queued until the next song is done playing.

    This command searches emby for a song
    """

    function = lambda chan: isinstance(chan, discord.TextChannel)
    mchan = dh.get_channel(ctx.guild, 'music', function)
    bchan = dh.get_channel(ctx.guild, 'bot', function)

    guild_id = str(ctx.guild.id)
    if guild_id not in self.info:
      self.info[guild_id] = {
        queue: deque(),
        chan:  mchan or bchan or ctx.channel,
        skip:  set(),
        np:    None,
      }

    if re.search('^(?:http|ftp|s?ftp)s?://', query):
      return await self.yt(ctx, query)
    else:
      return await self.emby_play(ctx, *shlex.split(query))

  async def emby_play(self, ctx, *search):
    qnext = False
    mult = False
    shuf = False
    albm = False
    num = 0
    gid = ctx.guild.id

    # parse arguments
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
            if flag == 'a':
              albm = True
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

    items = await self._search(search, albm)

    if not items:
      await self.bot.say(error('could not find song'))
      return False

    # pick display item (for "Queued: ..." message)
    if hasattr(items[0], 'songs') and await items[0].songs:
      display_item = items[0]
      items = await items[0].songs
    else:
      display_item = self.conn

    # filter non-music items
    items = [s for s in items if s.type == 'Audio']
    if not items:
      await self.bot.say(error('could not find song'))
      return

    # shuffle if needed (if user passed '-s')
    if shuf:
      random.shuffle(items)

    # TODO add to queue
    if mult:
      if num > 0:
        items = items[:num]
      ignore = 'Songs,Artists' if display_item is self.conn else 'Songs'
      em = await emby_helper.makeEmbed(display_item, 'Queued: ', ignore)

      songs_str = ''
      for i in items:
        if hasattr(i, 'index_number'):
          songs_str += f'{i.index_number:02} - {i.name}\n'
        else:
          songs_str += f'{i.name}\n'
        if qnext:
          self.info[gid]['queue'].appendleft(i)
        else:
          self.info[gid]['queue'].append(i)
      if qnext:
        songs_str = songs_str.split('\n')
        songs_str = '\n'.join(songs_str[::-1])
      if len(songs_str) >= 1024:
        songs_str = songs_str[:1020]+'\n...'
      em.add_field(name='Items', value=songs_str)
    else:
      item = random.choice(items)
      em = await emby_helper.makeEmbed(item, 'Queued: ', 'Songs')
      if qnext:
        self.info[gid]['queue'].appendleft(item)
      else:
        self.info[gid]['queue'].append(item)
    await self.bot.say(embed=em)

  async def yt(self, ctx, url):
    """Plays from a url (almost anything youtube_dl supports)"""
    gid = ctx.guild.id

    async with ctx.typing():
      self.info[gid]['queue'].append(url)
      await ctx.send('Queued: {}'.format(url))

  @music.command()
  async def volume(self, ctx, volume: int):
    """Changes the player's volume"""

    if ctx.voice_client is None:
      return await ctx.send("Not connected to a voice channel.")

    ctx.voice_client.source.volume = volume
    await ctx.send("Changed volume to {}%".format(volume))

  @music.command()
  async def stop(self, ctx):
    """Stops and disconnects the bot from voice"""

    await ctx.voice_client.disconnect()

  @play.before_invoke
  async def ensure_voice(self, ctx):
    if ctx.voice_client is None:
      if ctx.author.voice:
        await ctx.author.voice.channel.connect()
      else:
        await ctx.send("You are not connected to a voice channel.")
        raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
      ctx.voice_client.stop()



def search_f(terms, *items):
  logger.debug('search - starting search_f')
  out   = []
  terms = set(terms)
  for item in items:
    strings = set()
    for attr in ('artist_names', 'overview', 'path', 'genres', 'tags'):
      attribute = getattr(item, attr, '')
      if type(attribute) == list:
        attribute = ', '.join(attribute)
      if attribute:
        strings.add(attribute)
    if match(terms, item.id, item.name, *strings):
      out.append(item)
    logger.debug('  match end')
  logger.debug('search - found %d', len(out))
  return out

def match(patterns, *strings):
  logger.debug('match - "%s" "%s"', '; '.join(patterns), '; '.join(strings))
  for patt in patterns:
    if not patt:
      continue
    lowered = patt.lower()
    if strings[0].lower() == lowered: # ID matched
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
