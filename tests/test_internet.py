#!/usr/bin/env python3

import unittest
import asyncio
import os.path
import sys

import includes.internet as internet

class TestInternet(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_lmgtfy_query(self):
    url = internet.lmgtfy('test')
    self.assertIn('q=test', url, "Query not created for lmgtfy")

  def test_lmgtfy_general(self):
    url = internet.lmgtfy('test')
    self.assertIn('https://lmgtfy.com/', url, "lmgtfy does not work")

  def test_search_web(self):
    result = sync(internet.get_search_entries('google'))[0]
    self.assertIn('https://www.google.com/', result, "searching does not work")

  @unittest.removeHandler
  def test_search_as_calculator(self):
    result = sync(internet.get_search_entries('5+5*6'))[0]
    #TODO this needs to be implemented
    #self.assertIn('35', result, "searching does not calculate simple expression")

def sync(function):
  return asyncio.get_event_loop().run_until_complete(function)

if __name__ == '__main__':
  unittest.main()
