#!/usr/bin/env python3

import fnmatch
import random
import os

def find(directory, pattern, single=True):
  pattern = '*'+pattern.replace(' ', '*')+'*'
  matches = []
  
  for root, directories, filenames in os.walk(directory):
    for filename in filenames:
      filename = os.path.join(root,filename)
      filename = os.path.realpath(filename)
      if fnmatch.fnmatch(filename, pattern):
        matches.append(filename)
  
  if single:
    return random.choice(matches)
  return matches
