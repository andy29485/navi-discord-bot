#!/usr/bin/env python3

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
        d = json.load(f)
    except:
      d = {}
    for i in d:
      self.__setitem__(i, d[i])
  
  def save(self):
    with open(self.name, 'w') as f:
      json.dump(self.copy(), f)
    
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
    
