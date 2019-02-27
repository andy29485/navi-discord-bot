#!/usr/bin/env python3

import asyncio
import logging
from discord.ext import commands
from includes.utils.config import Config
import includes.utils.heap as heap

logger = logging.getLogger('navi.heap')

class HeapCog(commands.Cog):
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/heap.json')
    if 'heap' not in self.conf:
      self.conf['heap'] = heap.Heap()

    bot.loop.create_task(self.check_heap())

  async def check_heap(self):
    while self == self.bot.get_cog('HeapCog'):
      heap_popped = False
      # if there are valid items that expired/expire soon, process them
      while self.conf['heap'].time_left < 2:
        # remove item from heap
        item = self.conf['heap'].pop()
        logger.debug('popping item from heap (%s)', item.to_dict())

        await item.end(self.bot)   # perform its task
        heap_popped = True         # signify that a save is needed

      # only save heap to disk if an item was pop
      if heap_popped:
        self.conf.save()

      # wait a bit and check again
      await asyncio.sleep(min(self.conf['heap'].time_left, 30)+0.5)

  def index(self, item):
    return self.conf['heap'].index(item)

  async def push(self, item, *args, **kwargs):
    self.conf['heap'].push(item)
    await item.begin(*args, **kwargs)
    self.conf.save()

  def pop(self, item):
    self.conf['heap'].pop(item)
    self.conf.save()

  def __iter__(self):
    return self.conf['heap'].__iter__()

def setup(bot):
  h = HeapCog(bot)
  bot.add_cog(h)
