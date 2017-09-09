#!/usr/bin/env python3

import asyncio
from cogs.utils.config import Config
import cogs.utils.heap as heap

class HeapCog:
  def __init__(self, bot):
    self.bot  = bot
    self.conf = Config('configs/heap.json')
    if 'heap' not in self.conf:
      self.conf['heap'] = heap.Heap()

    bot.loop.create_task(self.check_heap())

  async def check_heap(self):
    while self == self.bot.get_cog('HeapCog'):
      print(1)
      heap_popped = False
      print(2)
      # if there are valid items that expired/expire soon, process them
      print(3)
      while self.conf['heap'].time_left < 2:
        print(4)
        item = self.conf['heap'].pop()   # remove item from heap
        print(5)
        await item.end(self.bot)         # perform its task
        print(6)
        heap_popped = True               # signify that a save is needed
        print(7)

      # only save heap to disk if an item was pop
      print(8)
      if heap_popped:
        print(9)
        self.conf.save()

      # wait a bit and check again
      print(10)
      await asyncio.sleep(min(self.conf['heap'].time_left, 30)+0.5)

def setup(bot):
  h = HeapCog(bot)
  bot.add_cog(h)
