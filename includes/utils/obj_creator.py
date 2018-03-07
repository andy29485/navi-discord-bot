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
  from cogs.utils.role_removals import RoleRemove
  from cogs.utils.reminders import Reminder
  from cogs.utils.timeout import Timeout
  from cogs.utils.heap import Heap
  from cogs.utils.poll import Poll

  if dct.get('__reminder__', False):
    return Reminder.from_dict(dct)
  elif dct.get('__poll__', False):
    return Poll.from_dict(dct)
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
  from cogs.utils.role_removals import RoleRemove
  from cogs.utils.reminders import Reminder
  from cogs.utils.timeout import Timeout
  from cogs.utils.heap import Heap, HeapNode
  from cogs.utils.poll import Poll
  return locals()[name]


class ObjEncoder(json.JSONEncoder):
  '''
  convert python obj to json obj
  supports same conversions as the function that goes the other way
  '''
  def default(self, obj):
    from cogs.utils.heap import Heap, HeapNode
    for dictable_type in (Heap, HeapNode):
      if isinstance(obj, dictable_type):
        return obj.to_dict()
    if type(obj) == set:
      return {'__set__':True, 'items':list(obj)}
    # Let the base class default method raise the TypeError
    return json.JSONEncoder.default(self, obj)
