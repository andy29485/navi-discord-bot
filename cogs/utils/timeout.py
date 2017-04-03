#!/usr/bin/env python3

import time
import asyncio
import cogs.utils.heap

# NOTE: depricated

class Timeout:
  def __init__(self,chan,serv,usr,roles,end_time,values=[],importing=False):
    self.channel_id = chan if importing else chan.id
    self.server_id  = serv if importing else serv.id
    self.user_id    = usr  if importing else usr.id
    self.roles      = roles if importing else []
    self.end_time   = time.time() + end_time
    self.start      = False
    if not importing:
      for role in roles:
        self.roles.append(role.id)
      for to in values:
        if to == self:
          return
      heap.insertInto(values, self)

  def __eq__(self, other):
   return self.server_id == other.server_id and self.user_id == other.user_id

  def __lt__(self, other):
   return self.end_time < other.end_time

  def __gt__(self, other):
   return self.end_time > other.end_time

  def to_dict(self):
   d = {'__timeout__':True}
   d['channel_id'] = self.channel_id
   d['server_id']  = self.server_id
   d['user_id']    = self.user_id
   d['roles']      = self.roles
   d['end_time']   = self.end_time
   return d

  def ready():

  async def end(self, bot):
    pass

  async def extend(self, bot):
    pass
