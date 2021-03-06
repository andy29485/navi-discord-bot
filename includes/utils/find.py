#!/usr/bin/env python3

import zipfile
import tempfile
import logging
import random
import os
import re
from includes.utils.config import Config

logger = logging.getLogger('navi.find')

# load config, for search term replacements
conf = Config('configs/az.json')

def search(directory, patterns, single=True):
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
  patterns = set(x for x in patterns if x)
  debugPts = set()
  tmp_pats = set()

  logger.debug('patts-in = {%s}', ', '.join(patterns))
  for pat in patterns:
    tmp = pat[0] + re.sub('[_ -]+', '_', pat[1:])

    for word,rep in conf.get('img-reps', {}).items():
      mtc = re.search(f'^(-?)(_?){word}(_?)$', tmp)
      if mtc:
        tmp = mtc.group(1)+mtc.group(2)+rep+mtc.group(3)
        break

    tmp = tmp.replace('.', '\\.')
    tmp = re.sub(r'(^\*+|\*+$)', '', tmp)
    tmp = re.sub(r'\*+', r'\\w*', tmp)
    tmp = re.sub(r'^(-?)_(.*)$', r'\1(\\b|_)\2', tmp)
    tmp = re.sub(r'^(.*)_$', r'\1(\\b|_)', tmp)
    tmp = re.sub(r'^-(.*)$', r'^((?!\1).)*$', tmp)

    debugPts.add(tmp)
    tmp_pats.add(re.compile(tmp))
  patterns = tmp_pats
  logger.debug('patterns = {%s}', ', '.join(debugPts))

  # create an empty list of matches(nothing matched yet)
  matches = []

  # traverse all files in location to search
  for root, directories, filenames in os.walk(directory):
    # ignore the git directory
    directories[:] = [d for d in directories if d and d[0] != '.']
    tmproot = root.replace(directory, '') # root dir for search only
    for name in filenames:
      if match(os.path.join(tmproot, name).lower(), patterns):
        matches.append(os.path.realpath(os.path.join(root, name)))
  logger.debug('matched %d files', len(matches))

  # if user wants only one file, choose and return at random
  # otherwise return all matches
  if single:
    return random.choice(matches)
  return matches

def match(filename, patterns):
  '''
  checks if a filename matches a specified pattern
  '''
  for pat in patterns:
    if not pat.search(filename): return False
  return True
