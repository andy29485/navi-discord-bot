#!/usr/bin/env python3

import re
import asyncio
import discord
import logging
import os
from os import stat
from git import Repo,Actor
from pwd import getpwuid
from cogs.utils import perms
import cogs.utils.format as formatter
from cogs.utils import find as azfind
from cogs.utils.config import Config
from cogs.utils import discord_helper as dh
from zipfile import ZipFile as zipfile

logger = logging.getLogger('navi.az')

class AZ:
  def __init__(self, test=False):
    self.last = {}
    self.conf = Config('configs/az.json', save=(not test))
    if 'lenny' not in self.conf:
      self.conf['lenny'] = {}
    if 'img-reps' not in self.conf:
      self.conf['img-reps'] = {}
    if 'repeat_after' not in self.conf:
      self.conf['repeat_after'] = 3
    self.conf.save()

  def lenny(self, first=''):
    out = None
    try:
      num = int(first)
      if num < 1:
        num = 1
      if num > 10:
        num = 10
    except:
      num = 1
      out = self.conf['lenny'].get(first.lower(), None)
    out = code(out) if out else '\n( ͡° ͜ʖ ͡° )'
    return out*num

  def shrug(self):
    return '¯\_(ツ)_/¯'

  def get_colour(self, colour):
    colour = colour.lower().strip()
    match  = re.search('^(0[hx])?([a-f0-9]{6})$', colour)
    if colour in dh.colours:
      c = dh.colours[colour]
    elif match:
      c = discord.Colour(int(match.group(2), 16))
    else:
      return None
    return c

  def img(self, *search):
    if not os.path.exists(self.conf.get('path', '')):
      logger.debug('could not find images')
      raise IOError('No images found')

    try:
      git_sync(self.conf.get('path'))
    except:
      pass

    search = [re.sub(r'[^\w\./#\*-]+', '', i).lower() for i in search]
    search = dh.remove_comments(search)

    try:
      path = azfind.search(self.conf['path'], search)
    except:
      path = ''

    if not path.strip():
      return None

    try:
      url = path.replace(self.conf['path'], self.conf['path-rep'])
      logger.info(url)
      if url.rpartition('.')[2] in ('gif', 'png', 'jpg', 'jpeg', 'zip', 'cbz'):
        try:
          em = discord.Embed()
          em.set_image(url=url)
          logger.debug(f'sending {str(em.to_dict())}')
          return em
        except:
          pass
      else:
        return url
    except:
      raise

def git_sync(path):
  # load repo
  repo   = Repo(path)
  git    = repo.git
  author = Actor('navi', 'navi@andy29485.tk')
  remote = repo.remotes[0]
  users  = set()
  logger.debug('sync - loaded git info')

  # check for changed files
  logger.debug('getting users')
  for fname in repo.untracked_files:
    fname = os.path.join(path, fname)
    uname = getpwuid(stat(fname).st_uid).pw_name
    users.add(uname)
  logger.debug('sync - found users: %s', ', '.join(users))

  # commit changes
  if users or repo.untracked_files:
    logger.debug('sync - adding files')
    git.add('-A')
    msg = f"navi auto add - {', '.join(unames or ['none'])}: added files"

    logger.debug('commiting')
    try:
      git.commit('-m', msg, f'--author="{author.name} <{author.email}>"')
      users = True # just in case
    except:
      users = False

  # sync with remote
  logger.debug('sync - pulling')
  remote.pull()
  if users:
    logger.debug('sync - pushing')
    remote.push()
