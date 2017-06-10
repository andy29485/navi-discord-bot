#!/usr/bin/env python3

from cogs.utils import puush
from discord import Embed
import hashlib
import asyncio

colours = [0x1f8b4c, 0xc27c0e, 0x3498db, 0x206694, 0x9b59b6,
           0x71368a, 0xe91e63, 0xe67e22, 0xf1c40f, 0x1abc9c,
           0x2ecc71, 0xa84300, 0xe74c3c, 0xad1457, 0x11806a]

async def makeEmbed(item, message=''):
  loop = asyncio.get_event_loop()
  em = Embed()
  img_url          = item.primary_image_url
  if 'https' in img_url:
    img_url        = await loop.run_in_executor(None,puush.get_url,img_url)
  em.title         = message+item.name
  try:
    em.description = item.overview
  except:
    em.description = item.media_type
  em.url           = item.url
  em.colour        = getColour(item.id)
  em.set_thumbnail(url=img_url)
  if hasattr(item, 'genres') and item.genres:
    em.add_field(name='Tags', value=', '.join(item.genres))
  if 'RunTimeTicks' in item.object_dict:
    d = int(float(item.object_dict['RunTimeTicks']) * (10**-7))
    if d > 1:
      d = '{:02}:{:02}:{:02}'.format(d//3600, d//60, d%60)
      em.add_field(name='Duration', value=d)
  return em

def getColour(string : str):
  str_hash = hashlib.md5()
  str_hash.update(string.strip().encode())
  str_hash = int(str_hash.hexdigest(), 16)
  return colours[str_hash % len(colours)]
