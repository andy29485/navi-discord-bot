#!/usr/bin/env python3

from discord import Embed
import hashlib
import asyncio
import requests
import aiohttp
import logging
from includes.utils.config import Config
from embypy import Emby as EmbyPy

logger = logging.getLogger('navi.emby_helper')

colours = [0x1f8b4c, 0xc27c0e, 0x3498db, 0x206694, 0x9b59b6,
           0x71368a, 0xe91e63, 0xe67e22, 0xf1c40f, 0x1abc9c,
           0x2ecc71, 0xa84300, 0xe74c3c, 0xad1457, 0x11806a]

conf = Config('configs/emby.json')

if 'address' not in conf or not conf['address']:
  conf['address'] = input('Enter emby url: ')
  conf.save()
if 'watching' not in conf or 'last' not in conf['watching']:
  conf['watching'] = {'last':None}
  conf.save()
if 'auth' not in conf or not conf['auth']:
  conf['auth'] = {}
  conf['auth']['api_key']   = input('Enter emby api key: ')
  conf['auth']['userid']    = input('Enter emby user id: ')
  conf['auth']['device_id'] = input('Enter emby device id: ')
  conf.save()

conn = EmbyPy(conf['address'], **conf['auth'], ws=False)

async def makeEmbed(item, message='', ignore=()):
  logger.debug('making embed - ' + str(item))
  loop = asyncio.get_event_loop()
  em = Embed()

  await item.update() # just in case

  if hasattr(item, 'index_number'):
    logger.debug('setting title w/ index')
    name = '{:02} - {}'.format(item.index_number, item.name)
  else:
    logger.debug('setting title w/o index')
    name = item.name or ''

  async with aiohttp.ClientSession() as session:
    if item.type == 'Audio':
      url = item.album_primary_image_url
    else:
      url = item.primary_image_url
    async with session.get(url,timeout=5) as img:
      logger.debug('checking image url')
      if img.status == 200:
        logger.debug('url ok')
        em.set_thumbnail(url=img.url)
      elif item.parent_id:
        logger.debug('using parent url')
        em.set_thumbnail(url=(await item.parent).primary_image_url)

  em.title  = (message+name or '<No name>').strip()

  if hasattr(item, 'series_name') and item.series_name:
    logger.debug('setting show name as description')
    season_num  = item.season_number
    episode_num = item.episode_number
    show_name   = item.series_name
    if season_num:
      str_ep = f'{show_name} - {season_num:02}x{episode_num:02}'
    else:
      str_ep = f'{item.season_name} - {episode_num:02}'
    em.set_footer(text=str_ep)

  if getattr(item, 'overview') and 'Overview' not in ignore:
    logger.debug('setting overview as description')
    if len(item.overview) > 250:
      des = item.overview[:247] + '...'
    else:
      des = item.overview
    em.description = des
  elif item.type:
    logger.debug('using type for description')
    em.description = item.type

  if item.id and 'Url' not in ignore:
    logger.debug('setting url')
    em.url = item.url

  if 'Colour' not in ignore:
    logger.debug('setting colour')
    em.colour = getColour(item.id)

  if 'artists' in dir(item) and 'Artists' not in ignore:
    logger.debug('setting artists')
    names = ', '.join(i.name for i in await item.artists)
    if len(names) > 250:
      names = names[:247]+'...'
    em.add_field(name='Artists', value=names)

  if 'album' in dir(item) and 'Album' not in ignore:
    logger.debug('setting album name')
    a = await item.album
    if a and a.name:
      em.add_field(name='Album', value=a.name)

  if getattr(item, 'genres') and 'Tags' not in ignore:
    logger.debug('setting genres')
    em.add_field(name='Tags', value=', '.join(item.genres))

  if item.object_dict.get('RunTimeTicks', None) and 'Duration' not in ignore:
    logger.debug('setting run time')
    d = int(float(item.object_dict.get('RunTimeTicks') / (10**7)))
    if d > 1:
      d = f'{d//3600:02}:{(d//60)%60:02}:{d%60:02}'
      em.add_field(name='Duration', value=d)

  if 'songs' in dir(item) and 'Songs' not in ignore:
    songs = ''
    for s in await item.songs:
      song = f'{s.index_number:02} - {s.name}\n'
      if len(songs)+len(song) > 800:
        songs += '...'
        break
      songs += song
    em.add_field(name='Songs', value=songs)

  logger.debug('done making embed - %s', str(em.to_dict()))
  return em

def getColour(string : str):
  str_hash = hashlib.md5()
  str_hash.update(string.strip().encode())
  str_hash = int(str_hash.hexdigest(), 16)
  return colours[str_hash % len(colours)]
