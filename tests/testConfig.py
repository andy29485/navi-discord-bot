#!/usr/bin/env python3

import unittest
import os.path
import sys

from cogs.utils.config import Config

class TestConfig(unittest.TestCase):
  config_name     = 'tests/test_config.json'
  config_name_alt = 'tests/test_save.json'

  def setUp(self):
    self.config = Config(TestConfig.config_name, save=False)

  def tearDown(self):
    Config.configs = {}
    if os.path.exists(TestConfig.config_name_alt):
      os.remove(TestConfig.config_name_alt)

  def test_empty(self):
    self.config = Config('does_not_exist', save=False)
    self.assertEqual(self.config, {}, "empty config not created")

  def test_keys(self):
    for key in "abcd":
      self.assertIn(key, self.config, "key missing in config")
    self.assertNotIn("e", self.config, "extra key present")

  def test_save(self):
    old_name = self.config.name
    self.config.name = TestConfig.config_name_alt
    self.config._save_force()
    self.config.name = old_name

    test_config = Config(TestConfig.config_name_alt, save=False)

    self.assertEqual(self.config, test_config, "saving does not work")

  def test_object_encode(self): #TODO
    pass

  def test_object_decode(self): #TODO
    pass

  def test_get(self):
    self.assertEqual(self.config.get("a"), 10, "get method failed")

  def test_brace_get(self):
    self.assertEqual(self.config["b"], [1,2,3], "get using brackets failed")

  def test_delete(self):
    del self.config["a"]
    self.assertNotIn("a", self.config, "key not deleted")

  def test_set(self):
    self.config["new"] = "testing insert"
    self.assertEqual(self.config.get("new"), "testing insert", "insert failed")

if __name__ == '__main__':
  unittest.main()
