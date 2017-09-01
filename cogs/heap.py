#!/usr/bin/env python3

import asyncio
from cogs.utils.config import Config
import cogs.utils.heap as heap

class HeapCog:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = heap.conf
    if 'heap' not in self.conf:
      self.conf['heap'] = heap.Heap()

    bot.loop.create_task(self.check_heap())

  async def check_heap(self):
    while self == self.bot.get_cog('HeapCog'):
      heap_popped = False
      # if there are valid items that expired/expire soon, process them
      while self.conf['heap'].time_left < 2:
        item = self.conf['heap'].pop()   # remove item from heap
        await item.end(self.bot) # perform its task
        heap_popped = True       # signify that a save is needed

      # only save heap to disk if an item was pop
      if heap_popped:
        self.conf.save()

      # wait a bit and check again
      await asyncio.sleep(min(self.conf['heap'].time_left, 30)+0.5)

def setup(bot):
  h = HeapCog(bot)
  bot.add_cog(h)
