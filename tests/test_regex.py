#!/usr/bin/env python3

import unittest
import asyncio
import os.path
import sys

import includes.regex as regex

class TestRegex(unittest.TestCase):
  def setUp(self):
    self.regex = regex.Regex(test=True)

  def tearDown(self):
    pass

  def test_compile_re_good(self):
    self.assertTrue(regex.comp('hello'), "simple regex is bad")
    self.assertTrue(regex.comp('([a-z]+h)?e\\s+.*'), "valid regex not working")

  def test_compile_re_bad(self):
    self.assertFalse(regex.comp('([a-z+h)?e\\s+.*'), "bad regex works")

  def test_replace_works(self):
    self.regex.add('s/cat/chomusuke/')
    replacement = self.regex.replace('this is a cat')
    self.assertEquals('this is a chomusuke', replacement, "rep not working")

  def test_replace_does_not_spam(self):
    self.regex.add('s/cat/chomusuke/')
    self.regex.add('s/bat/chomusuke/')
    replacement = self.regex.replace('this is a mat')
    self.assertEquals(None, replacement, 'rep spams everything')

if __name__ == '__main__':
  unittest.main()
