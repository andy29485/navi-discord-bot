#!/usr/bin/env python3

import re
import time
import cogs.utils.heap as heap
import datetime

class Reminder:
  tm = [re.compile(r'[T _-]*(?P<hour>\d\d?):(?P<min>\d\d)'+
                  r'(:(?P<sec>\d\d))?(\s+(?P<meridiem>[APap][Mm]))?'
        )
       ]
  dt = [re.compile(r'(?P<year>\d{4})-(?P<month>\d\d)-(?P<day>\d\d)'),
        re.compile(r'(?P<month>\d{1,2})[/\.-](?P<day>\d{1,2})'+
                   r'[/\.-](?P<year>\d\d(\d\d)?)'
        )
       ]
  def __init__(self, channel_id, user_id, message, end_time=0):
    self.channel_id = channel_id
    self.user_id    = user_id
    self.message    = message
    self.end_time   = end_time
    if not end_time:
      self.parse_time()

  def __lt__(self, other):
    return self.end_time < other.end_time

  def __gt__(self, other):
    return self.end_time > other.end_time

  def is_ready(self):
    return self.end_time <= time.time()

  def get_message(self):
    return '{}: {}'.format(self.user_id, self.message)

  def __repr__(self):
    return str(self.end_time)

  def parse_time(self):
    offset = time.time()
    times = {
         '(?i)(\\d+)\\s*s(econds?)?'    : 1,
         '(?i)(\\d+)\\s*m(in(ute)?s?)?' : 60,
         '(?i)(\\d+)\\s*h(ours?)?'      : 3600,
         '(?i)(\\d+)\\s*d(ays?)?'       : 86400,
         '(?i)(\\d+)\\s*w(eeks?)?'      : 604800,
         '(?i)(\\d+)\\s*months?'        : 2628000
    }
    m_time = None
    m_date = None
    if re.search(r'(?i)^(me)?\s*at', self.message):
      date_time = datetime.datetime.today()
      for t in Reminder.tm:
        m_time = t.search(self.message)
        if m_time:
          if m_time.group('hour'):
            h = int(m_time.group('hour'))
            if str(m_time.group('meridiem')).lower() == 'pm':
              h += 12
            date_time = date_time.replace(hour=h)
          if m_time.group('min'):
            m = int(m_time.group('min'))
            date_time = date_time.replace(minute=m)
          if m_time.group('sec'):
            s = int(m_time.group('sec'))
            date_time = date_time.replace(second=s)
          self.message = self.message.replace(m_time.group(0), '')
          break
      for d in Reminder.dt:
        m_date = d.search(self.message)
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
          self.message = self.message.replace(m_date.group(0), '')
          break
      if m_time or m_date:
        offset = date_time.timestamp()
    if not re.search(r'(?i)^(me)?\s*at',self.message) or not (m_date or m_time):
      for t in times:
        match = re.search(t, self.message)
        self.message = re.sub(t, '', self.message).strip()
        if match:
          offset += times[t]*float(match.group(1))
    self.message = re.sub(r'(?i)^(me\s+)?(at|in)?\s*', '', self.message).strip()
    self.end_time = offset

  def to_dict(self):
    dct = {'__reminder__':'true'}
    dct['channel_id'] = self.channel_id
    dct['user_id']    = self.user_id
    dct['message']    = self.message
    dct['end_time']   = self.end_time
    return dct

  def insertInto(self, values):
    heap.insertInto(values, self)

  def popFrom(self, values):
    return heap.popFrom(values)
