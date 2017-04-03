#!/usr/bin/env python3

def insertInto(values, item):
  i = len(values)
  values.append(item)
  pushUp(values, i)

def popFrom(values):
  largest   = values[0]
  size      = len(values)-1
  if size == 0:
    values.pop()
  elif size > 0:
    values[0] = values.pop()
    pushDown(values, 0, size-1)
  return largest

def pushUp(values, index, first = 0):
  parent = (index-1)//2;

  while parent >= first and values[index] < values[parent]:
    values[index], values[parent] = values[parent], values[index];

    index  = parent;
    parent = (index-1)//2;

def pushDown(values, index, last = 0):
  if not last:
    last = len(values)-1

  left  = 2*index + 1
  right = 2*index + 2
  small = index

  small = small if (left >last or values[small]<values[left])  else left
  small = small if (right>last or values[small]<values[right]) else right

  if small != index:
    values[small], values[index] = values[index], values[small]
    pushDown(values, small, last)
