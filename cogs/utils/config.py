#!/usr/bin/env python3

from cogs.utils.reminders import Reminder
from cogs.utils.timeout import Timeout
import json

class Config(dict):
  def __init__(self, name, *args, **kw):
    super(Config,self).__init__(*args, **kw)
    self.name = name
    self.load()
    self.save()

  def load(self):
    self.clear()
    try:
      with open(self.name, 'r') as f:
        d = json.load(f, object_hook=as_obj)
    except:
      d = {}
    for i in d:
      self.__setitem__(i, d[i])

  def save(self):
    with open(self.name, 'w') as f:
      json.dump(self.copy(), f, cls=ObjEncoder)

  def __setitem__(self, key, value):
    super(Config,self).__setitem__(key, value)
    self.save()

  def __delitem__(self, key):
    super(Config,self).__delitem__(key)
    self.save()

  def __iter__(self):
    return super(Config,self).__iter__()

  def keys(self):
    return super(Config,self).keys()

  def values(self):
    return [self[key] for key in self]

  def itervalues(self):
    return (self[key] for key in self)

def as_obj(dct):
  if '__reminder__' in dct:
    return Reminder(dct['channel_id'], dct['user_id'],
                    dct['message'], end_time=dct['end_time']
    )
  elif '__timeout__' in dct:
    return Reminder(dct['channel_id'], dct['server_id'], dct['user_id'],
                    dct['roles'], dct['end_time'], importing=True
    )
  return dct

class ObjEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Reminder):
      return obj.to_dict()
    if isinstance(obj, Timeout):
      return obj.to_dict()
    # Let the base class default method raise the TypeError
    return json.JSONEncoder.default(self, obj)
