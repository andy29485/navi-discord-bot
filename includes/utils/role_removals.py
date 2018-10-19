#!/usr/bin/env python3

import time
import logging
import includes.utils.heap as heap
from includes.utils import discord_helper as dh

logger = logging.getLogger('navi.role_rm')

class RoleRemove(heap.HeapNode):
  def __init__(self, end_time, role_id, auth_id, chan_id, serv_id):
    self.end_time= end_time
    self.role_id = str(getattr(role_id, 'id', role_id))
    self.serv_id = str(getattr(serv_id, 'id', serv_id))
    self.auth_id = str(getattr(auth_id, 'id', auth_id))
    self.chan_id = str(getattr(chan_id, 'id', chan_id))

  @staticmethod
  def from_dict(dct):
    end_time = dct.get('end_time')
    role_id  = dct.get('role_id')
    serv_id  = dct.get('serv_id')
    auth_id  = dct.get('auth_id')
    chan_id  = dct.get('chan_id')

    return RoleRemove(end_time, role_id, auth_id, chan_id, serv_id)

  def to_dict(self):
    '''
    convert this timeout object to a dictionary
    used for exporting to json
    '''
    d = {'__role_rem__':True}
    d['end_time'] = self.end_time
    d['role_id']  = self.role_id
    d['serv_id']  = self.serv_id
    d['auth_id']  = self.auth_id
    d['chan_id']  = self.chan_id
    return d

  # ==
  def __eq__(self, other):
    return type(self)   == type(other)   and \
           self.role_id == other.role_id and \
           self.serv_id == other.serv_id and \
           self.auth_id == other.auth_id

  # <
  def __lt__(self, other):
    return self.end_time < other.end_time

  # >
  def __gt__(self, other):
    return self.end_time > other.end_time

  async def begin(self, bot):
    for index,role in enumerate(self.heap):
      if self is not role and self == role:
        self.heap.pop(index)
        break

  async def end(self, bot):
    serv = bot.get_guild(       self.serv_id) # get server info
    auth = dh.get_user(   serv, self.auth_id) # get author info
    chan = dh.get_channel(serv, self.chan_id) # get channel info
    role = dh.get_role(   serv, self.role_id) # get role info

    # remove the role
    await auth.remove_roles(role)

    # create a message, and report that role has been removed
    msg = f"{auth.mention}: role {role.name} has been removed"
    await chan.send(msg)
