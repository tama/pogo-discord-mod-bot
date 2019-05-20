import unittest

from mod_bot.raid import clean_raid_command, clean_empty_parts, fix_lone_at_sign, fix_lone_exclamation_sign


class TestRaidCreation(unittest.TestCase):

    def test_clean_spaces(self):
        words = ["!raid", " ", "egg5", "arena", "@20h00"]
        self.assertEqual(clean_empty_parts(words), ["!raid", "egg5", "arena", "@20h00"])

    def test_fix_lone_at_sign(self):
        words = ["!raid", " ", "egg5", "arena", "@", "20h00"]
        self.assertEqual(fix_lone_at_sign(words), ["!raid", " ", "egg5", "arena", "@20h00"])

    def test_fix_lone_exclamation_sign(self):
        words = ["!", "raid", " ", "egg5", "arena", "@20h00"]
        self.assertEqual(fix_lone_exclamation_sign(words), ["!raid", " ", "egg5", "arena", "@20h00"])

    def test_clean_raid_command(self):
        words = ["!", "raid", "", "egg5", "arena", "@", "20h00"]
        self.assertEqual(clean_raid_command(words), ["!raid", "egg5", "arena", "@20h00"])
