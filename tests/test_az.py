#!/usr/bin/env python3

import unittest
import asyncio
import os.path
import sys

import includes.az as az

class TestRegex(unittest.TestCase):
  def setUp(self):
    self.az = az.AZ(test=True)

  def tearDown(self):
    pass

  def test_one_lenny(self):
    self.assertEqual('\n( ͡° ͜ʖ ͡° )', self.az.lenny(), 'no arg lenny failing')

  def test_many_lenny(self):
    self.assertEqual('\n( ͡° ͜ʖ ͡° )'*5, self.az.lenny(5),'multi-lenny failing')

if __name__ == '__main__':
  unittest.main()
