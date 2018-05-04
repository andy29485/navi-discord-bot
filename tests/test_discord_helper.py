#!/usr/bin/env python3

import unittest
import datetime
import monthdelta
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
      a = datetime.datetime.fromtimestamp(a)
      b = datetime.datetime.fromtimestamp(b)
      self.assertEqual(a, b, msg)

  def test_offset_h(self):
    result    = dh.get_end_time('me in 5 h message')
    date_time = datetime.datetime.today() + datetime.timedelta(hours=5)
    ts        = date_time.timestamp()
    message   = "offset +5h"
    self.assertAboutEqual(result[0], ts,  message+' - timestamp')
    self.assertEqual(result[1],    'message', message+' - message')
    self.assertItemsEqual(result[2], ['5 h'], message+' - match')

  def test_offset_hm(self):
    result    = dh.get_end_time('me in 5 hours 3 m message')
    date_time = datetime.datetime.today()+datetime.timedelta(hours=5,minutes=3)
    ts        = date_time.timestamp()
    message   = "offset +5h, +3m"
    self.assertAboutEqual(result[0], ts,            message+' - timestamp')
    self.assertEqual(result[1],             'message',  message+' - message')
    self.assertItemsEqual(result[2], ['5 hours','3 m'], message+' - match')


  def test_offset_w(self):
    result    = dh.get_end_time('me 1 week message')
    date_time = datetime.datetime.today() + datetime.timedelta(days=7)
    ts        = date_time.timestamp()
    message   = "offset +1 week"
    self.assertAboutEqual(result[0], ts,     message+' - timestamp')
    self.assertEqual(result[1],      'message',  message+' - message')
    self.assertItemsEqual(result[2], ['1 week'], message+' - match')


  def test_offset_monthA(self):
    result    = dh.get_end_time('me 7 months message')
    date_time = datetime.datetime.today() + monthdelta.monthdelta(7)
    ts        = date_time.timestamp()
    message   = "offset +7 months (me)"
    self.assertAboutEqual(result[0], ts,       message+' - timestamp')
    self.assertEqual(result[1],        'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7 months'], message+' - match')


  def test_offset_monthB(self):
    result    = dh.get_end_time('in 7 months message')
    date_time = datetime.datetime.today() + monthdelta.monthdelta(7)
    ts        = date_time.timestamp()
    message   = "offset +7 months (in)"
    self.assertAboutEqual(result[0], ts,       message+' - timestamp')
    self.assertEqual(result[1],        'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7 months'], message+' - match')


  def test_dateA(self):
    result    = dh.get_end_time('me at 2017-10-23 message')
    date_time = datetime.datetime.today().replace(
      year=2017,
      month=10,
      day=23,
    )
    ts = date_time.timestamp()
    message = "date (2017-10-23)"
    self.assertAboutEqual(result[0], ts,         message+' - timestamp')
    self.assertEqual(result[1],          'message',  message+' - message')
    self.assertItemsEqual(result[2], ['2017-10-23'], message+' - match')


  def test_timestampA(self):
    result    = dh.get_end_time('me at 2017-10-23T05:11:56 message')
    date_time = datetime.datetime.today().replace(
      year=2017,
      month=10,
      day=23,
      hour=5,
      minute=11,
      second=56,
    )
    ts = date_time.timestamp()
    match   = ['2017-10-23','T05:11:56']
    message = "timestamp (2017-10-23T05:11:56)"
    self.assertAboutEqual(result[0], ts,   message+' - timestamp')
    self.assertEqual(result[1],     'message', message+' - message')
    self.assertItemsEqual(result[2], match,    message+' - match')


  def test_timestampB(self):
    result    = dh.get_end_time('at 2017-10-23 05:11:56 message')
    date_time = datetime.datetime.today().replace(
      year=2017,
      month=10,
      day=23,
      hour=5,
      minute=11,
      second=56,
    )
    ts = date_time.timestamp()
    match   = ['2017-10-23', '05:11:56']
    message = "timestamp (2017-10-23 05:11:56)"
    self.assertAboutEqual(result[0], ts,   message+' - timestamp')
    self.assertEqual(result[1],     'message', message+' - message')
    self.assertItemsEqual(result[2], match,    message+' - match')


  def test_timestampC(self):
    result    = dh.get_end_time('at 10/23/2017 5:11 PM message')
    date_time = datetime.datetime(
      year=2017,
      month=10,
      day=23,
      hour=17,
      minute=11,
    )
    ts = date_time.timestamp()
    match   = ['10/23/2017', '5:11 PM']
    message = "timestamp (10/23/2017 5:11 PM)"
    self.assertAboutEqual(result[0], ts,   message+' - timestamp')
    self.assertEqual(result[1],     'message', message+' - message')
    self.assertItemsEqual(result[2], match,    message+' - match')


  def test_time_hm(self):
    result    = dh.get_end_time('at 7:11 message')
    message   = "time hour:min"
    dt        = datetime.datetime.fromtimestamp(result[0])
    self.assertEqual(dt.hour,              7,  message+' - hour')
    self.assertEqual(dt.minute,           11,  message+' - minute')
    self.assertEqual(result[1],    'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7:11'], message+' - match')


  def test_time_hms(self):
    result    = dh.get_end_time('at 7:11:15 message')
    message   = "time hour:min:sec"
    dt        = datetime.datetime.fromtimestamp(result[0])
    self.assertEqual(dt.hour,                 7,  message+' - hour')
    self.assertEqual(dt.minute,              11,  message+' - minute')
    self.assertEqual(dt.second,              15,  message+' - second')
    self.assertEqual(result[1],       'message',  message+' - message')
    self.assertItemsEqual(result[2], ['7:11:15'], message+' - match')

if __name__ == '__main__':
  unittest.main()
