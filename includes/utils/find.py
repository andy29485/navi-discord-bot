#!/usr/bin/env python3

import zipfile
import tempfile
import logging
import random
import os
from cogs.utils.config import Config

logger = logging.getLogger('navi.find')

# load config, for search term replacements
conf = Config('configs/az.json')

def search(directory, pattern, single=True):
  '''
  searches all file in a directory for a set of patterns

  if a pattern starts with a hyphen("-") it will be negatively matched

  if "single" is false, all matched are returned
  otherwise only one will be returned at random(default behaviour)

  Note: if a ".git" dir is present, it will not be searched
  '''
  # remove duplicates from pattern,
  # convert all strings to lowercase,
  # and remove empty strings
  pattern = set([x.lower() for x in pattern if x])

  # replaces each of the search terms so that more things get found)
  for word,rep in conf.get('img-reps', {}).items(): # for each rep-able word
    if word in pattern:                             #   if it's being searched
      pattern.add(rep)                              #     remove it
      pattern.remove(word)                          #     add replacement

  # create an empty list of matches(nothing matched yet)
  matches = []

  # traverse all files in location to search
  for root, directories, filenames in os.walk(directory):
    # ignore the git directory
    directories[:] = [d for d in directories if d not in ['.git']]
    for filename in filenames:
      filename = os.path.realpath(os.path.join(root, filename)) # get full path
      if match(filename.lower(), pattern): # if file matches pattern,
        matches.append(filename)           #   add it to the list of matches

  # if user wants only one file, choose and return at random
  # otherwise return all matches
  if single:
    return random.choice(matches)
  return matches

def match(filename, pattern):
  '''
  checks if a filename matches a specified pattern
  '''
  for i in pattern:         # for each pattern
    if i[0] == '-':         # if it's a negative match pattern,
      if i[1:] in filename: #   return false it it's found in the filename
        return False
    elif i not in filename: # otherwise return false if it's NOT found
      return False
  return True               # return true at the end, since all test succeeded
