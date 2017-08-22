#!/usr/bin/env python3

import time

class RoleStruct:
  def __init__(self, end_time, role_id, auth_id, chan_id, serv_id):
    self.end_time= end_time
    self.role_id = getattr(role_id, 'id', role_id)
    self.serv_id = getattr(serv_id, 'id', serv_id)
    self.auth_id = getattr(auth_id, 'id', auth_id)
    self.chan_id = getattr(chan_id, 'id', chan_id)

  # ==
  def __eq__(self, other):
    return self.role_id == other.role_id and \
           self.serv_id == other.serv_id and \
           self.auth_id == other.auth_id

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
    d['auth_id']  = self.auth_id
    d['chan_id'] = self.chan_id
    return d

  @property
  def time_left(self):
    '''
    return number of seconds left
    '''
    return self.end_time - time.time()
