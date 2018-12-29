#!/usr/bin/env python3

import abc
import time
import logging
import heapq
from includes.utils.config import Config
import includes.utils.obj_creator as obj_creator

logger = logging.getLogger('navi.heapclass')

# a few functions which manipulate a given list as if it was a heap
# smallest items "float" up to the top of the heap
# also two classes that will be used as a heap comtainer and heap nodes

class Heap:
  '''
  container heap class
  '''
  def __init__(self, items = []):
    '''
    create a heap, using constr as the class for new object creation
    '''
    for item in items:
      item.heap = self
    self.items  = heapq.heapify(items)

  def __iter__(self):
    return self.items.__iter__()

  def __repr__(self):
    h = self.__hash__()
    return f"<heap {h} {self.items}>"

  @staticmethod
  def from_dict(dct):
    items = [obj_creator.as_obj(i) if type(i) == dict else i
                for i in dct.get('items', [])
    ]
    return Heap(items)

  def to_dict(self):
    return {
      '__heap__':'true',
      'items': self.items
    }

  @property
  def time_left(self):
    if len(self.items) == 0:
      return float('inf')
    return self.items[0].time_left

  def index(self, item):
    for index,i in enumerate(self.items):
      if i == item:
        return index

  def push(self, item):
    '''
    insert an item into the heap
    '''
    item.heap = self        # create pointer to self
    heapq.heappush(self.items, item) # push it

    #i = len(self.items)     # get the to-be-index of the to-be-inserted item

    #self.items.append(item) # append it
    #self._pushUp(i)         # move it up to the position that it should be in

  def pop(self, index=0):
    '''
    returns the top item in the heap(and removes it from the heap)

    if an index is given, then that item will be removed
    '''
    val  = self.items[index]   # get a refference to the item(temp variable)
    size = len(self.items)     # get the to-be-total-size of the heap
    if size == 1:              # if there is only one items
      return self.items.pop()  #   return that item
    else:
      # otherwise move the last item to the position of the requested item,
      # then push the recently moved item down to where it should go
      self.items[index] = self.items.pop()
      self.items = heapq.heapify(self.items)
    return val

  def _pushUp(self, index, first = 0):
    '''
    push an item up the heap to where it should be

    index:  index of the item to push up
    first:  index of the highest item in the heap(not to go up past)
    '''
    parent = (index-1)//2 # first get the index of the parent item

    # while the parent is not too high(not past the root/first index)
    #       and the parent is smaller than the item
    #   swap the parent/item
    #   set new item index to parent index
    #   recalculate the parent inex
    while parent >= first and self.items[index] < self.items[parent]:
      self.items[index],self.items[parent]=self.items[parent],self.items[index]

      index  = parent
      parent = (index-1)//2

  def _pushDown(self, index, last = 0):
    '''
    push an item up the heap to where it should be

    index:  index of the item to push up
    first:  index of the highest item in the heap(not to go up past)
    '''
    # calculate the index of the last item if it's not given
    if not last:
      last = len(self.items)-1

    # caluculate indices of child nodes left/right of(to?) current
    left  = 2*index + 1
    right = 2*index + 2
    small = index       # for starters assume the current node is the smallest

    # then find the smallest node of the three
    small=small if(left >last or self.items[small]<self.items[left]) else left
    small=small if(right>last or self.items[small]<self.items[right])else right

    # if the current node is not the smallest, then a push down is needed
    if small != index:
      # swap the smallest child with the index
      self.items[small],self.items[index] = self.items[index],self.items[small]
      # then attempt to push down again
      self._pushDown(small, last)


class HeapNode:
  def __init__(self, end_time=0):
    self.end_time = end_time
    self.heap     = None

  @staticmethod
  def from_dict(dct):
    raise NotImplementedError('The from_dict function must be defined')

  @abc.abstractmethod
  def to_dict(self):
    raise NotImplementedError('The to_dict function must be defined')

  @abc.abstractmethod
  def __eq__(self):
    raise NotImplementedError('The __eq__ function must be defined')

  @abc.abstractmethod
  def __lt__(self):
    raise NotImplementedError('The __lt__ function must be defined')

  @abc.abstractmethod
  def __gt__(self):
    raise NotImplementedError('The __gt__ function must be defined')

  @property
  def time_left(self):
    '''
    return number of seconds left
    '''
    return self.end_time - time.time()

  @abc.abstractmethod
  async def begin(self, bot):
    raise NotImplementedError('The begin function must be defined')

  @abc.abstractmethod
  async def end(self, bot):
    raise NotImplementedError('The end function must be defined')
