#!/usr/bin/env python3

import arrow
import discord
import logging
import time
import re

logger = logging.getLogger('navi.dh')

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
   r'(?i)(\d+)\s*s(econds?)?\b'       : 'seconds',
   r'(?i)(\d+)\s*m(in(ute)?s?)?\b'    : 'minutes',
   r'(?i)(\d+)\s*(an\s+)?h(ours?)?\b' : 'hours',
   r'(?i)(\d+)\s*d(ays?)?\b'          : 'days',
   r'(?i)(\d+)\s*w(eeks?)?\b'         : 'weeks',
   r'(?i)(\d+)\s*months?\b'           : 'months',
   r'(?i)(\d+)\s*years?\b'            : 'years',
}
day_ex  = r'(\s*the)?\s*(?P<day>\d\d?)\s*(th|st|rd|nd)?(\s*of)?(?=[^a-z0-9:])'
year_ex = r'\s*(-|,|of|in)?(\s*the\s*year)?(\s*of)?\s*(?P<year>\d{4})\b'
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

colours = {
  'teal' : discord.Colour.teal(),
  'dark_teal' : discord.Colour.dark_teal(),
  'green' : discord.Colour.green(),
  'dark_green' : discord.Colour.dark_green(),
  'blue' : discord.Colour.blue(),
  'dark_blue' : discord.Colour.dark_blue(),
  'purple' : discord.Colour.purple(),
  'dark_purple' : discord.Colour.dark_purple(),
  'magenta' : discord.Colour.magenta(),
  'dark_magenta' : discord.Colour.dark_magenta(),
  'gold' : discord.Colour.gold(),
  'dark_gold' : discord.Colour.dark_gold(),
  'orange' : discord.Colour.orange(),
  'dark_orange' : discord.Colour.dark_orange(),
  'red' : discord.Colour.red(),
  'dark_red' : discord.Colour.dark_red(),
  'lighter_grey' : discord.Colour.lighter_grey(),
  'dark_grey' : discord.Colour.dark_grey(),
  'light_grey' : discord.Colour.light_grey(),
  'darker_grey' : discord.Colour.darker_grey()
}

def get_end_time(message, start_date=arrow.now()):
  # datetime -> arrow compatibility fix
  if type(start_date) != arrow.arrow.Arrow:
    start_date = arrow.get(start_date)

  datestrs  = []                     # list of matched strings
  m_time    = None                   # tmp var: matched time (w/o date)
  m_date    = None                   # tmp var: matched date (w/o time)
  date_time = start_date             # defaults for unmatched parts/final

  # remove filler words from message
  message = re.sub(r'(?i)^\s*(me|remove|end)?\s*(at|[oi]n)?\s*', '', message)
  message = message.strip()

  # check if a day of week (mon[0]..sun[6]) was mentioned
  for num, day_pattern in enumerate(dow_names):
    m_date = day_pattern.search(message)
    if m_date: # week day matched
      # get min number days until the next wanted day
      offset=(7+num-date_time.weekday())%7 #offset=(7+want-now)%7
      date_time = date_time.shift(days=offset)
      # if a day of month was also specified
      if m_date.group('day'):
        day = int(m_date.group('day'))
        for i in range(0,53):
          # look for the next Xth dow that falls on the Yth dom
          date_time_tmp = date_time.shift(weeks=i)
          if date_time_tmp.day == day:
            date_time = date_time_tmp
            break
      # remove match from message, and save matched string
      message = message.replace(m_date.group(0), '', 1)
      datestrs.append(m_date.group(0))
      m_date = {x:y for x,y in m_date.groupdict().items() if y}
      m_date.update({'dow':num})
      break

  # if weekday was not matched, try looking for a date
  if not m_date:
    # look for month names
    for num, month in enumerate(month_names, 2):
      num = num//2 # because each month has 2 patterns, enumerate needs a fix
      m_date = month.search(message)
      if m_date:
        # if matched replace default month name
        date_time = date_time.replace(month=num)
        if m_date.group('day'):
          # if day of month was also matched, replace that too
          day = int(m_date.group('day'))
          date_time = date_time.replace(day=day)
        if m_date.group('year'):
          # if year was also matched, replace that too
          year = int(m_date.group('year'))
          date_time = date_time.replace(year=year)
        # if date has passed, try to resolve it
        while date_time.date() < start_date.date():
          if not m_date.group('year'):
            # if user says `remind me in march` on march 4th,
            #   they probably care about next year's march
            date_time = date_time.shift(years=1)
          elif not m_date.group('day'):
            date_time = date_time.shift(days=1)
          else:
            # can't do anything, reminder is already expired
            # issue will propogate and resolve itself later
            # TODO - maybe just return here?
            break
        # remove match from message, and save matched string
        message = message.replace(m_date.group(0), '')
        datestrs.append(m_date.group(0))
        m_date = {x:y for x,y in m_date.groupdict().items() if y}
        break

  # if weekday AND month names don't match, search for other date strings
  if not m_date:
    for pattern in dt:
      m_date = pattern.search(message)
      if m_date:
        # if year part is matched, replace default
        if m_date.group('year'):
          y = int(m_date.group('year'))
          date_time = date_time.replace(year=y)
        # if month part is matched, replace default
        if m_date.group('month'):
          m = int(m_date.group('month'))
          date_time = date_time.replace(month=m)
        # if day part is matched, replace default
        if m_date.group('day'):
          d = int(m_date.group('day'))
          date_time = date_time.replace(day=d)
        # remove match from message and save matched string
        message = message.replace(m_date.group(0), '')
        datestrs.append(m_date.group(0))
        m_date = {x:y for x,y in m_date.groupdict().items() if y}
        break

  # remove trash from message yet again
  message = re.sub(r'(?i)^\s*(at|[oi]n)?\s*', '', message).strip()

  # search for time part in message
  for pattern in tm:
    m_time = pattern.search(message)
    if m_time:
      if m_time.group('hour'):
        h = int(m_time.group('hour'))
        mer = str(m_time.group('meridiem')).lower()
        # for the americans
        if mer[0] == 'p':
          if h < 12:
            h += 12
        elif mer[0] == 'a':
          if h == 12:
            h = 0
        date_time = date_time.replace(hour=h)
      # replace default minute if specified
      if m_time.group('min'):
        m = int(m_time.group('min'))
        date_time = date_time.replace(minute=m)
      else:
        # zero is a better default
        date_time = date_time.replace(minute=0)
      # replace default second if specified
      if m_time.group('sec'):
        s = int(m_time.group('sec'))
        date_time = date_time.replace(second=s)
      else:
        # zero is a better default
        date_time = date_time.replace(second=0)
      # remove match from message, and save matched string
      message = message.replace(m_time.group(0), '')
      datestrs.append(m_time.group(0))
      m_time = {x:y for x,y in m_time.groupdict().items() if y}
      break

  if m_time or m_date:
    found_groups = (m_time or {})
    found_groups.update(m_date or {})
    # shift the times to find the next matching time that works/not expired
    while date_time <= start_date.shift(seconds=5):
      if 'day' not in found_groups:
        shift = 7 if 'dow' in found_groups else 1
        date_time = date_time.shift(days=shift)
      elif 'month' not in found_groups:
        date_time = date_time.shift(months=1)
      elif 'year' not in found_groups:
        date_time = date_time.shift(years=1)
      else:
        break
  else:
    # if no dates / times were found, look for offsets
    #   e.g "[in ]8 minutes"
    for t in times:
      match = re.search(t, message)
      if match:
        date_time = date_time.shift(**{times[t]:float(match.group(1))})
        datestrs.append(match.group(0))
        message = message.replace(match.group(0), '')

  # return the timestamp, cleaned message, and a list of matched strings
  return date_time.timestamp, message.strip(), datestrs

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
  try:
    if match:
      user = server.get_member(match.group(1))
      if user and (not function or function(user)):
        return user
  except:
    pass

  match = name_pattern.match(search_param)
  name  = match.group(1) if match else search_param.lower()
  discr = match.group(2) if match else ''

  try:
    members = server.members
  except:
    members = server.get_all_members()

  for user in members:
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
