import unittest

from mod_bot.main import clean_whitespaces, clean_at_sign


class TestRaidCreation(unittest.TestCase):

    def test_clean_spaces(self):
        words = ["!raid", " ", "egg5", "arena", "@20h00"]
        self.assertEqual(clean_whitespaces(words), ["!raid", "egg5", "arena", "@20h00"])

    def test_clean_at_sign(self):
        words = ["!raid", " ", "egg5", "arena", "@", "20h00"]
        self.assertEqual(clean_at_sign(words), ["!raid", " ", "egg5", "arena", "20h00"])
