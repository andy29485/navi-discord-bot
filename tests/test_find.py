#!/usr/bin/env python3

import unittest
import asyncio
import os.path
import sys

import includes.utils.find as find

class TestRegex(unittest.TestCase):
  path = 'tests/find/'

  def srch(self, *argv, **karg):
    return find.search(TestRegex.path, *argv, **karg)

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_find_all(self):
    self.assertEqual(14, len(self.srch([], 0)), 'find all issue')

  def test_find_none(self):
    self.assertEqual(0, len(self.srch(['dne'], 0)), 'find none issue')

  def test_find_root(self):
    self.assertEqual(1, len(self.srch(['g'], 0)), 'find in root issue')

  def test_find_by_dir(self):
    self.assertEqual(2, len(self.srch(['d/'], 0)), 'find by dir issue')

  def test_find_in_subdir(self):
    self.assertEqual(1, len(self.srch(['h'], 0)), 'find in subdir issue')

  def test_find_in_mult_subdir(self):
    self.assertEqual(6, len(self.srch(['c'], 0)), 'find multi in subdir issue')

  def test_find_negative(self):
    self.assertEqual(8, len(self.srch(['-c'], 0)), 'find negative issue')

  def test_find_bound_dd(self):
    self.assertEqual(1, len(self.srch(['_word1_'], 0)), 'bound dd issue')

  def test_find_bound_du(self):
    self.assertEqual(1, len(self.srch(['_word2_'], 0)), 'bound du issue')

  def test_find_bound_uu(self):
    self.assertEqual(1, len(self.srch(['_word3_'], 0)), 'bound uu issue')

  def test_find_bound_ue(self):
    self.assertEqual(1, len(self.srch(['_word4_'], 0)), 'bound ue issue')

if __name__ == '__main__':
  unittest.main()
