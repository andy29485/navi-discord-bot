#!/usr/bin/env python3

import datetime
import monthdelta
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
   r'(?i)(\d+)\s*s(econds?)?\b'    : 1,
   r'(?i)(\d+)\s*m(in(ute)?s?)?\b' : 60,
   r'(?i)(\d+)\s*h(ours?)\b?'      : 3600,
   r'(?i)(\d+)\s*d(ays?)?\b'       : 86400,
   r'(?i)(\d+)\s*w(eeks?)?\b'      : 604800,
   r'(?i)(\d+)\s*months?\b'        : 2628000
}
day_ex  = r'(\s*the)?\s*(?P<day>\d\d?)\s*(th|st|rd|nd)?(\s*of)?\b'
year_ex = r'\s*(,|of|in)?(\s*the\s*year)?(\s*of)?\s*(?P<year>\d{4})\b'
dow_names = [ #monday=0,...,sunday=6
  re.compile(f'(?i)^\\s*mon(day)?({day_ex})?\\b'),
  re.compile(f'(?i)^\\s*tue(s(day)?)?({day_ex})?\\b'),
  re.compile(f'(?i)^\\s*wed(nes(day)?)?({day_ex})?\\b'),
  re.compile(f'(?i)^\\s*thu(r(s(day)?)?)?({day_ex})?\\b'),
  re.compile(f'(?i)^\\s*fri(day)?({day_ex})?\\b'),
  re.compile(f'(?i)^\\s*sat(ur(day?))?({day_ex})?\\b'),
  re.compile(f'(?i)^\\s*sun(day)?({day_ex})?\\b')
]
month_names = [
  re.compile(f'(?i)({day_ex})\\s*jan(uary)?\\s*({year_ex})?'),
  re.compile(f'(?i)jan(uary)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*feb(ruary)?\\s*({year_ex})?'),
  re.compile(f'(?i)feb(ruary)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*mar(ch)?\\s*({year_ex})?'),
  re.compile(f'(?i)mar(ch)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*apr(il?)\\s*?({year_ex})?'),
  re.compile(f'(?i)apr(il?)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*may(\\s*{year_ex})?'),
  re.compile(f'(?i)may\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*june?(\\s*{year_ex})?'),
  re.compile(f'(?i)june?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*july?(\\s*{year_ex})?'),
  re.compile(f'(?i)july?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*aug(u(st)?\\s*)?({year_ex})?'),
  re.compile(f'(?i)aug(u(st)?)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*sep(t(em(ber)?\\s*)?)?({year_ex})?'),
  re.compile(f'(?i)sep(t(em(ber)?)?)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*oct(o(ber)?\\s*)?({year_ex})?'),
  re.compile(f'(?i)oct(o(ber)?)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*nov(em(ber)?\\s*)?({year_ex})?'),
  re.compile(f'(?i)nov(em(ber)?)?\\s*{day_ex}\\s*({year_ex})?'),
  re.compile(f'(?i)({day_ex})\\s*dec(em(ber)?\\s*)?({year_ex})?'),
  re.compile(f'(?i)dec(em(ber)?)?\\s*{day_ex}\\s*({year_ex})?')
]

def get_end_time(message):
  datestrs = []
  offset   = time.time()
  m_time   = None
  m_date   = None
  date_time = datetime.datetime.today()
  message = re.sub(r'(?i)^\s*(me|remove|end)?\s*(at|[oi]n)?\s*',
                   '', message
  ).strip()
  for num, day in enumerate(dow_names):
    m_date = day.search(message)
    if m_date:
      offset=(7+num-date_time.weekday())%7 #offset=(7+want-now)%7
      date_time += datetime.timedelta(days=offset)
      if m_date.group('day'):
        day = int(m_date.group('day'))
        for i in range(1,53):
          date_time_tmp = date_time+datetime.timedelta(weeks=i)
          if date_time_tmp.day == day:
            date_time = date_time_tmp
            break
      message = message.replace(m_date.group(0), '')
      datestrs.append(m_date.group(0))
      break
  if not m_date:
    for num, month in enumerate(month_names, 2):
      num = num//2
      m_date = month.search(message)
      if m_date:
        date_time = date_time.replace(month=num)
        if m_date.group('day'):
          day = int(m_date.group('day'))
          date_time = date_time.replace(day=day)
        if m_date.group('year'):
          year = int(m_date.group('year'))
          date_time = date_time.replace(year=year)
        while date_time < datetime.datetime.today():
          if not m_date.group('year'):
            date_time += monthdelta.monthdelta(12)
          elif not m_date.group('day'):
            date_time += datetime.timedelta(days=1)
          else:
            break
        message = message.replace(m_date.group(0), '')
        datestrs.append(m_date.group(0))
        break
  if not m_date:
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
          while date_time < datetime.datetime.today():
            if not m_date.group('year'):
              date_time += monthdelta.monthdelta(12)
            elif not m_date.group('day'):
              date_time += datetime.timedelta(days=1)
            else:
              break
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
      while date_time < datetime.datetime.today():
        if not m_time.group('hour'):
          date_time += datetime.timedelta(hours=1)
        elif not m_date or not m_date.group('day'):
          date_time += datetime.timedelta(days=1)
        elif not m_date.group('month'):
          date_time += monthdelta.monthdelta(1)
        elif not m_date.group('year'):
          date_time += monthdelta.monthdelta(12)
        else:
          break
      message = message.replace(m_time.group(0), '')
      datestrs.append(m_time.group(0))
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


def get_user(server, search_param, function=None):
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
    if user and (not function or function(user)):
      return user

  match = id_pattern.match(search_param)
  if match:
    user = server.get_member(match.group(1))
    if user and (not function or function(user)):
      return user

  match = name_pattern.match(search_param)
  name  = match.group(1) if match else search_param.lower()
  discr = match.group(2) if match else ''

  for user in server.members:
    if name == user.name and discr in str(user.discriminator):
      if not function or function(user):
        return user
    if name in (user.name.lower(), (user.nick or '').lower()):
      if not function or function(user):
        return user

  return None

def get_role(server, search_param, function=None):
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
      if not function or function(role):
        return role

  return None

def get_channel(server, search_param, function=None):
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
    if search_param in (str(chan.id), chan.name.lower()):
      if not function or function(chan):
        return chan

  return None
