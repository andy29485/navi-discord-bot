#!/usr/bin/env python3

import unittest
import arrow
import includes.utils.discord_helper as dh

class TestConfig(unittest.TestCase):

  def setUp(self):
    self.err_margin = 5

  def tearDown(self):
    pass

  def assertItemsEqual(self, a, b, msg=''):
    self.assertEqual(len(a), len(b), msg)
    self.assertEqual(set(a), set(b), msg)

  def assertAboutEqual(self, a, b, msg=''):
    try:
      self.assertLessEqual(abs(a-b), self.err_margin, msg)
    except:
      a = arrow.get(a)
      b = arrow.get(b)
      self.assertEqual(a, b, msg)

  def test_offset_h(self):
    result    = dh.get_end_time('me in 5 h message')
    date_time = arrow.now().shift(hours=5)
    ts        = date_time.timestamp
    message   = "offset +5h"
    self.assertAboutEqual(result[0],     ts,  message+' - timestamp')
    self.assertEqual(result[1],    'message', message+' - message')
    self.assertItemsEqual(result[2], ['5 h'], message+' - match')

  def test_offset_hm(self):
    result    = dh.get_end_time('me in 5 hours 3 m message')
    date_time = arrow.now().shift(hours=5,minutes=3)
    ts        = date_time.timestamp
    message   = "offset +5h, +3m"
    self.assertAboutEqual(result[0],               ts,  message+' - timestamp')
    self.assertEqual(result[1],             'message',  message+' - message')
    self.assertItemsEqual(result[2], ['5 hours','3 m'], message+' - match')


  def test_offset_w(self):
    result    = dh.get_end_time('me 1 week message')
    date_time = arrow.now().shift(days=7)
    ts        = date_time.timestamp
    message   = "offset +1 week"
    self.assertAboutEqual(result[0], ts,     message+' - timestamp')
    self.assertEqual(result[1],      'message',  message+' - message')
    self.assertItemsEqual(result[2], ['1 week'], message+' - match')


  def test_offset_monthA(self):
    result    = dh.get_end_time('me 7 months message')
    date_time = arrow.now().shift(months=7)
    ts        = date_time.timestamp
    message   = "offset +7 months (me)"
    self.assertAboutEqual(result[0],          ts,  message+' - timestamp')
    self.assertEqual(result[1],        'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7 months'], message+' - match')


  def test_offset_monthB(self):
    result    = dh.get_end_time('in 7 months message')
    date_time = arrow.now().shift(months=7)
    ts        = date_time.timestamp
    message   = "offset +7 months (in)"
    self.assertAboutEqual(result[0],          ts,  message+' - timestamp')
    self.assertEqual(result[1],        'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7 months'], message+' - match')


  def test_dateA(self):
    result    = dh.get_end_time('me at 2017-10-23 message')
    date_time = arrow.now().replace(
      year=2017,
      month=10,
      day=23,
    )
    ts = date_time.timestamp
    message = "date (2017-10-23)"
    self.assertAboutEqual(result[0],            ts,  message+' - timestamp')
    self.assertEqual(result[1],          'message',  message+' - message')
    self.assertItemsEqual(result[2], ['2017-10-23'], message+' - match')


  def test_timestampA(self):
    result    = dh.get_end_time('me at 2017-10-23T05:11:56 message')
    date_time = arrow.now().replace(
      year=2017,
      month=10,
      day=23,
      hour=5,
      minute=11,
      second=56,
    )
    ts = date_time.timestamp
    match   = ['2017-10-23','T05:11:56']
    message = "timestamp (2017-10-23T05:11:56)"
    self.assertAboutEqual(result[0],      ts,  message+' - timestamp')
    self.assertEqual(result[1],     'message', message+' - message')
    self.assertItemsEqual(result[2], match,    message+' - match')


  def test_timestampB(self):
    result    = dh.get_end_time('at 2017-10-23 05:11:56 message')
    date_time = arrow.now().replace(
      year=2017,
      month=10,
      day=23,
      hour=5,
      minute=11,
      second=56,
    )
    ts = date_time.timestamp
    match   = ['2017-10-23', '05:11:56']
    message = "timestamp (2017-10-23 05:11:56)"
    self.assertAboutEqual(result[0],      ts,  message+' - timestamp')
    self.assertEqual(result[1],     'message', message+' - message')
    self.assertItemsEqual(result[2], match,    message+' - match')


  def test_timestampC(self):
    result    = dh.get_end_time('at 10/23/2017 5:11 PM message')
    date_time = arrow.now().replace(
      year=2017,
      month=10,
      day=23,
      hour=17,
      minute=11,
      second=0,
    )
    ts = date_time.timestamp
    match   = ['10/23/2017', '5:11 PM']
    message = "timestamp (10/23/2017 5:11 PM)"
    self.assertAboutEqual(result[0],      ts,  message+' - timestamp')
    self.assertEqual(result[1],     'message', message+' - message')
    self.assertItemsEqual(result[2], match,    message+' - match')


  def test_time_hm(self):
    result    = dh.get_end_time('at 7:11 message')
    message   = "time hour:min"
    dt        = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.hour,              7,  message+' - hour')
    self.assertEqual(dt.minute,           11,  message+' - minute')
    self.assertEqual(result[1],    'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7:11'], message+' - match')


  def test_time_hms(self):
    result    = dh.get_end_time('at 7:11:15 message')
    message   = "time hour:min:sec"
    dt        = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.hour,                 7,  message+' - hour')
    self.assertEqual(dt.minute,              11,  message+' - minute')
    self.assertEqual(dt.second,              15,  message+' - second')
    self.assertEqual(result[1],       'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7:11:15'], message+' - match')

  def test_weekday_day_before_dow_hm(self):
    start   = arrow.get('2018-05-03 8:00', 'YYYY-M-D H:mm')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('on friday 8:00 message', start)
    message = "dow hour:min - day before"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                  4, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],       'message', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00'], message+' - match')

  def test_weekday_min_before_dow_hm(self):
    start   = arrow.get('2018-05-04 7:59', 'YYYY-M-D H:mm')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('on friday 8:00 message', start)
    message = "dow hour:min - min before"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                  4, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],       'message', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00'], message+' - match')

  def test_weekday_sec_before_dow_hm(self):
    start   = arrow.get('2018-05-04 7:59:50', 'YYYY-M-D H:mm:ss')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('on friday 8:00 message', start)
    message = "dow hour:min - min before"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                 11, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],       'message', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00'], message+' - match')

  def test_weekday_at_dow_hm(self):
    start   = arrow.get('2018-05-04 8:00', 'YYYY-M-D H:mm')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('on friday 8:00 message', start)
    message = "dow hour:min - exact at"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                 11, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],       'message', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00'], message+' - match')

  def test_weekday_sec_after_dow_hm(self):
    start   = arrow.get('2018-05-04 8:00:01', 'YYYY-M-D H:mm:ss')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('on friday 8:00 message', start)
    message = "dow hour:min - sec after"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                 11, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],       'message', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00'], message+' - match')

  def test_weekday_sec_after_dow_hm_with_param(self):
    start   = arrow.get('2018-05-04 8:00:01', 'YYYY-M-D H:mm:ss')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('me on friday at 8:00:00 -r read:', start)
    message = "dow hour:min - sec after with param"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                 11, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],      '-r read:', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00:00'], message+' - match')

  def test_weekday_hour_after_dow_hm(self):
    start   = arrow.get('2018-05-04 9:00', 'YYYY-M-D H:mm')
    start   = start.replace(tzinfo=arrow.now().tzinfo)
    result  = dh.get_end_time('on friday 8:00 message', start)
    message = "dow hour:min - hour after"
    dt      = arrow.get(result[0]).to(arrow.now().tzinfo)
    self.assertEqual(dt.weekday(),            4, message+' - weekday')
    self.assertEqual(dt.day,                 11, message+' - day of month')
    self.assertEqual(dt.hour,                 8, message+' - hour')
    self.assertEqual(dt.minute,               0, message+' - minute')
    self.assertEqual(result[1],       'message', message+' - message')
    self.assertItemsEqual(result[2], ['friday', '8:00'], message+' - match')

if __name__ == '__main__':
  unittest.main()
