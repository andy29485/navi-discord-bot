#!/usr/bin/env python3

import os
import json
import logging
from cogs.utils.obj_creator import as_obj, ObjEncoder

logger = logging.getLogger('navi.config')

class Config(dict):
  configs = {}

  # object creation override,
  #   if another config with the same name(file) is open, return that instead
  def __new__(cls, name, save=True, *args, **kwargs):
    if name not in cls.configs:
      cls.configs[name] = super(Config, cls).__new__(cls)
    cls.configs[name]._save = save
    return cls.configs[name]

  def __init__(self, name, save=True, *args, **kwargs):
    '''
    load config from file, also test save just in case
    '''
    super(Config, self).__init__(*args, **kwargs)
    self.name  = name
    self._save = save
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
    if self._save:       # If object should be saved
      self._save_force() #   save it

  # force a save even if config says not to
  def _save_force(self):
    dirname = os.path.dirname(self.name)
    if not os.path.exists(dirname):
      os.makedirs(dirname)
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
