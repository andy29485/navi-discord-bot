#!/usr/bin/env python3

import json
import logging

logger = logging.getLogger('navi.obj_creater')

def as_obj(dct):
  '''
  convert json obj to python obj
  currently supports:
    - Reminders
    - Timeouts
  '''
  from includes.utils.role_removals import RoleRemove
  from includes.utils.reminders import Reminder
  from includes.utils.timeout import Timeout
  from includes.utils.heap import Heap

  if dct.get('__reminder__', False):
    return Reminder.from_dict(dct)
  elif dct.get('__timeout__', False):
    return Timeout.from_dict(dct)
  elif dct.get('__role_rem__', False):
    return RoleRemove.from_dict(dct)
  elif dct.get('__heap__', False):
    return Heap.from_dict(dct)
  elif dct.get('__set__', False):
    return set(dct['items'])
  return dct

def get_type(name):
  from includes.utils.role_removals import RoleRemove
  from includes.utils.reminders import Reminder
  from includes.utils.timeout import Timeout
  from includes.utils.heap import Heap, HeapNode
  return locals()[name]


class ObjEncoder(json.JSONEncoder):
  '''
  convert python obj to json obj
  supports same conversions as the function that goes the other way
  '''
  def default(self, obj):
    from includes.utils.heap import Heap, HeapNode
    for dictable_type in (Heap, HeapNode):
      if isinstance(obj, dictable_type):
        return obj.to_dict()
    if type(obj) == set:
      return {'__set__':True, 'items':list(obj)}
    # Let the base class default method raise the TypeError
    return json.JSONEncoder.default(self, obj)
