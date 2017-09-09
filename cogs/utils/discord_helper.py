#!/usr/bin/env python3

import datetime
import discord
import time
import re

id_pattern   = re.compile('<?[@#][!&]?([0-9]{15,21})>?')
name_pattern = re.compile('^<?@?(.+)#(\\d{4})>?$')

tm = [re.compile(r'[T _-]*(?P<hour>\d\d?):(?P<min>\d\d)'+
               r'(:(?P<sec>\d\d))?(\s*(?P<meridiem>[APap]\.?[Mm]\.?))?'
      )
]
dt = [re.compile(r'(?P<year>\d{4})-(?P<month>\d\d)-(?P<day>\d\d)'),
      re.compile(r'(?P<month>\d{1,2})[/\.-](?P<day>\d{1,2})'+
               r'[/\.-](?P<year>\d\d(\d\d)?)'
      )
]
times = {
   '(?i)(\\d+)\\s*s(econds?)?'    : 1,
   '(?i)(\\d+)\\s*m(in(ute)?s?)?' : 60,
   '(?i)(\\d+)\\s*h(ours?)?'      : 3600,
   '(?i)(\\d+)\\s*d(ays?)?'       : 86400,
   '(?i)(\\d+)\\s*w(eeks?)?'      : 604800,
   '(?i)(\\d+)\\s*months?'        : 2628000
}

def get_end_time(message):
  datestrs = []
  offset   = time.time()
  m_time   = None
  m_date   = None
  date_time = datetime.datetime.today()
  for d in dt:
    m_date = d.search(message)
    if m_date:
      if m_date.group('year'):
        y = int(m_date.group('year'))
        date_time = date_time.replace(year=y)
      if m_date.group('month'):
        m = int(m_date.group('month'))
        date_time = date_time.replace(month=m)
      if m_date.group('day'):
        d = int(m_date.group('day'))
        date_time = date_time.replace(day=d)
      message = message.replace(m_date.group(0), '')
      datestrs.append(m_date.group(0))
      break
  for t in tm:
    m_time = t.search(message)
    if m_time:
      if m_time.group('hour'):
        h = int(m_time.group('hour'))
        mer = str(m_time.group('meridiem')).lower()
        if mer[0] == 'p':
          if h < 12:
            h += 12
        elif mer[0] == 'a':
          if h == 12:
            h = 0
        date_time = date_time.replace(hour=h)
      if m_time.group('min'):
        m = int(m_time.group('min'))
        date_time = date_time.replace(minute=m)
      if m_time.group('sec'):
        s = int(m_time.group('sec'))
        date_time = date_time.replace(second=s)
      message = message.replace(m_time.group(0), '')
      datestrs.append(m_time.group(0))
      if offset>date_time.timestamp()and not(m_date and m_date.group('day')):
        # if user specified time(hour/minute) that has already happened today
        # (and no date was given)
        #   for example it is 11:00, but user wants 10:00
        # then use that time, but increment the day by one
        date_time += datetime.timedelta(days=1)
      break
  if m_time or m_date:
    offset = date_time.timestamp()
  else:
    for t in times:
      match = re.search(t, message)
      if match:
        offset += times[t]*float(match.group(1))
        datestrs.append(match.group(0))
        message = message.replace(match.group(0), '')
  message = re.sub(r'(?i)^(me|remove|end)?\s*(at|in)?\s*', '', message).strip()
  return int(offset), message, datestrs

def remove_comments(words):
  for i in range(len(words)):
    if re.search('^(//|#)', words[i]):
      words = words[:i]
      break

  for i in range(len(words)):
    if re.search('^(/\\*)', words[i]):
      for j in range(i, len(words)):
        if re.search('^(\\*/)', words[j]):
          break
      words = words[:i] + words[j+1:]
      break
  return words


def get_user(server, search_param):
  '''
  return user matching params in server
  search_param can be:
    - id as a string or int
    - @mention of the user
    - username#discriminator (name#0000 - not server nickname)
      - note: this has to be the discord username
      - note: case sensitive(unlike other options)
    - username
    - server nickname
  '''
  if hasattr(server, 'message'):  # if ctx was passed instead of a server
    server = server.message.server
  elif hasattr(server, 'server'): # if a message was passed instead of a server
    server = server.server

  if type(search_param) == int or re.match(r'\d+$', search_param):
    user = server.get_member(str(search_param))
    if user:
      return user

  match = id_pattern.match(search_param)
  if match:
    user = server.get_member(match.group(1))
    if user:
      return user

  match = name_pattern.match(search_param)
  name  = match.group(1) if match else search_param.lower()
  discr = match.group(2) if match else ''

  for user in server.members:
    if name == user.name and discr in str(user.discriminator):
      return user
    if name in (user.name.lower(), (user.nick or '').lower()):
      return user

  return None

def get_role(server, search_param):
  '''
  return role matching params in server
  search_param can be:
    - id as a string or int
    - @mention of the role
    - role name
  '''
  if hasattr(server, 'message'):  # if ctx was passed instead of a server
    server = server.message.server
  elif hasattr(server, 'server'): # if a message was passed instead of a server
    server = server.server

  if type(search_param) == int:
    search_param = str(search_param)
  else:
    match = id_pattern.match(search_param)
    search_param = match.group(1) if match else search_param.lower()

  for role in server.roles:
    if search_param in (str(role.id), role.name.lower()):
      return role

  return None

def get_channel(server, search_param):
  '''
  return channel matching params in server
  search_param can be:
    - id as a string or int
    - #mention of the channel
    - channel name
  '''
  chans = []
  if hasattr(server, 'message'):  # if ctx was passed instead of a server
    chans  = server.bot.get_all_channels()
    server = server.message.server
  elif hasattr(server, 'server'): # if a message was passed instead of a server
    server = server.server

  if type(search_param) == int or re.match(r'\d+$', search_param):
    search_param = str(search_param)
  else:
    match = id_pattern.match(search_param)
    search_param = match.group(1) if match else search_param.lower()

  if server:
    chans = server.channels
    chan  = server.get_channel(search_param)
    if chan:
      return chan


  for chan in chans:
    if search_param in (str(role.id), role.name.lower()):
      return chan

  return None
