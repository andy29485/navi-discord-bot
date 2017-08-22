#!/usr/bin/env python3

import json


class Config(dict):
  configs = {}

  # object creation override,
  #   if another config with the same name(file) is open, return that instead
  def __new__(cls, name, *args, **kwargs):
    if name not in cls.configs:
      cls.configs[name] = super(Config, cls).__new__(cls)
    return cls.configs[name]

  # load config from file, also test save just in case
  def __init__(self, name, *args, **kwargs):
    super(Config, self).__init__(*args, **kwargs)
    self.name = name
    self.load()
    self.save()

  # reload config from file
  def load(self):
    self.clear()                             # remove any info stored in dict
    try:
      with open(self.name, 'r') as f:        # open associated file
        d = json.load(f, object_hook=as_obj) # and parse it as a json file
    except:                                  #   see `as_obj` function
      d = {}                                 # on failure, empty dict is used
    self.update(d)                           # copy temp dict to self

  # save config to file
  def save(self):
    with open(self.name, 'w') as f:             # open associated file
      json.dump(self.copy(), f, cls=ObjEncoder) # and save as json
                                                #   see `ObjEncoder` class

  # on edit [top level only] save to file
  def __setitem__(self, key, value):
    super(Config,self).__setitem__(key, value)
    self.save()

  # on delete [top level only] save to file
  def __delitem__(self, key):
    super(Config,self).__delitem__(key)
    self.save()

def as_obj(dct):
  '''
  convert json obj to python obj
  currently supports:
    - Reminders
    - Timeouts
  '''
  from cogs.utils.role_removals import RoleStruct
  from cogs.utils.reminders import Reminder
  from cogs.utils.timeout import Timeout
  if '__reminder__' in dct:
    return Reminder(dct['channel_id'], dct['user_id'],
                    dct['message'], end_time=dct['end_time']
    )
  elif '__timeout__' in dct:
    return Timeout(dct['channel_id'], dct['server_id'], dct['user_id'],
                    dct['end_time'], dct['roles'], importing=True
    )
  elif '__role_rem__' in dct:
    return RoleStruct(dct['end_time'],  dct['role_id'],
                      dct['author_id'], dct['channel_id'], dct['serv_id']
    )
  return dct

# convert python obj to json obj
# supports same conversions as the function that goes the other way
class ObjEncoder(json.JSONEncoder):
  def default(self, obj):
    from cogs.utils.role_removals import RoleStruct
    from cogs.utils.reminders import Reminder
    from cogs.utils.timeout import Timeout

    if isinstance(obj, Reminder):
      return obj.to_dict()
    elif isinstance(obj, Timeout):
      return obj.to_dict()
    elif isinstance(obj, RoleStruct):
      return obj.to_dict()
    # Let the base class default method raise the TypeError
    return json.JSONEncoder.default(self, obj)
