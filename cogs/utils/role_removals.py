#!/usr/bin/env python3

import time

class RoleStruct:
  def __init__(self, end_time, role_id, author_id, channel_id, serv_id):
    self.end_time   = end_time
    self.role_id    = getattr(role_id,    'id',     role_id)
    self.serv_id    = getattr(serv_id,    'id',     serv_id)
    self.author_id  = getattr(author_id,  'id',   author_id)
    self.channel_id = getattr(channel_id, 'id',  channel_id)

  # ==
  def __eq__(self, other):
    return self.role_id   == other.role_id and \
           self.serv_id   == other.serv_id and \
           self.author_id == other.author_id

  # <
  def __lt__(self, other):
    return self.end_time < other.end_time

  # >
  def __gt__(self, other):
    return self.end_time > other.end_time

  def to_dict(self):
    '''
    convert this timeout object to a dictionary
    used for exporting to json
    '''
    d = {'__role_rem__':True}
    d['end_time']   = self.end_time
    d['role_id']    = self.role_id
    d['serv_id']    = self.serv_id
    d['author_id']  = self.author_id
    d['channel_id'] = self.channel_id
    return d

  @property
  def end_time():
    return self.end_time
  
  @property
  def role_id():
    return self.role_id

  @property
  def serv_id():
    return self.serv_id

  @property
  def channel_id():
    return self.channel_id

  @property
  def author_id():
    return self.author_id

  @property
  def time_left():
    '''
    return number of seconds left
    '''
    return self.end_time - time.time()
