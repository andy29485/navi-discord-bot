#!/usr/bin/env python3

import re
import logging
from includes.utils import format as formatter
from includes.utils import perms
from includes.utils.config import Config

logger = logging.getLogger('navi.regex')

class Regex:
  def __init__(self, test=False):
    self.replacements = Config('configs/replace.json', save=(not test))
    self.permissions  = Config('configs/perms.json',   save=(not test))
    if 'rep-blacklist' not in self.permissions:
      self.permissions['rep-blacklist'] = []

  def add(self, regex, author_id=''):
    #Find requested replacement
    rep = get_match(regex)

    #ensure that replace was found before proceeding
    if not rep:
      return formatter.error('Could not find valid regex')

    p1 = formatter.escape_mentions(rep.group(2))
    p2 = formatter.escape_mentions(rep.group(4))

    #check regex for validity
    if not comp(p1, p2):
      return formatter.error('regex is invalid')

    #make sure that there are no similar regexes in db
    for i in self.replacements:
      if similar(p1, i):
        r = '\"{}\" -> \"{}\"'.format(i, self.replacements[i][0])
        message = 'Similar regex already exists, delete or edit it\n{}'.format(
                   formatter.inline(r))
        return formatter.error(message)

    #make sure regex is not too broad
    if bad_re(p1):
      return formatter.error('regex is too broad')

    #check that regex does not already exist
    if p1 in self.replacements:
      return formatter.error('regex already exists')

    self.replacements[p1] = [p2, author_id]
    return formatter.ok()

  def edit(self, regex, author_id=''):
    #Find requested replacement
    rep = get_match(regex)

    #ensure that replace was found before proceeding
    if not rep:
      return formatter.error('Could not find valid regex')

    p1 = formatter.escape_mentions(rep.group(2))
    p2 = formatter.escape_mentions(rep.group(4))

    #check regex for validity
    if not comp(p1, p2):
      return formatter.error('regex is invalid')

    #make sure regex is not too broad
    if bad_re(p1):
      return formatter.error('regex is too broad')

    #ensure that replace was found before proceeding
    if p1 not in self.replacements:
      return formatter.error('Regex not in replacements.')

    #check if they have correct permissions
    if author_id != self.replacements[p1][1] \
       and not perms.is_owner_check(author_id):
        #will uncomment next line when reps are a per server thing
        #and not perms.check_permissions(ctx.message, manage_messages=True):
        raise commands.errors.CheckFailure('Cannot edit')

    self.replacements[p1] = [p2, author_id]
    return formatter.ok()

  def rm(self, pattern, author_id=''):
    #pattern = re.sub('^(`)?\\(\\?[^\\)]*\\)', '\\1', pattern)
    pattern = formatter.escape_mentions(pattern)

    #ensure that replace was found before proceeding
    if re.search('^`.*`$', pattern) and pattern[1:-1] in self.replacements:
      pattern = pattern[1:-1]
    elif pattern not in self.replacements:
      return formatter.error('Regex not in replacements.')

    #check if they have correct permissions
    if author_id != self.replacements[pattern][1] \
       and not perms.is_owner_check(author_id):
      raise commands.errors.CheckFailure('Cannot delete')

    self.replacements.pop(pattern)
    self.replacements.save()
    return formatter.ok()

  def ls(self):
    msg = '\n'.join(f'{k} -> {v}' for k,v in self.replacements.items())
    return formatter.code(msg)

  def replace(self, message):
    rep = message
    for i in self.replacements:
      rep = re.sub(r'(?i)\b{}\b'.format(i), self.replacements[i][0], rep)

    if rep.lower() != message.lower():
      return rep
    return None

  def is_banned(self, author_id):
    return author_id in self.permissions['rep-blacklist']

def get_match(string):
  pattern = r'^s{0}(\(\?i\))?(.*?[^\\](\\\\)*){0}(.*?[^\\](\\\\)*){0}g?$'
  sep = re.search('^s(.)', string)
  if not sep or len(sep.groups()) < 1 or len(sep.group(1)) != 1:
    return None
  return re.match(pattern.format(sep.group(1)), string)

def simplify(pattern):
  out = set()
  reps = [r'\s+']
  string_a = pattern
  for r in reps:
    string_a = re.sub(r, '', string_a)
    out.add(re.sub(r, '', pattern))
    out.add(string_a)
  return out

def similar(pattern1, pattern2):
  for sim1 in simplify(pattern1):
    for sim2 in simplify(pattern2):
      if (sim1.lower() == sim2.lower() or \
         re.search(r'(?i)\b{}\b'.format(pattern1), sim2) or \
         re.search(r'(?i)\b{}\b'.format(pattern2), sim1) or \
         (comp(sim1, sim2) and re.search(r'(?i)\b{}\b'.format(sim1), sim2)) or\
         (comp(sim2, sim1) and re.search(r'(?i)\b{}\b'.format(sim2), sim1))):
          return True
  return False

def bad_re(pattern):
  return max(len(s) for s in simplify(pattern)) < 3

def comp(regex, replace=''):
  try:
    re.sub(regex, replace, '')
    return True
  except:
    return False
