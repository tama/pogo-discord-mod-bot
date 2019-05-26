import unittest

from mod_bot import raid
from datetime import time
from datetime import datetime
import pytz


class TestRaidCreation(unittest.TestCase):
    global now
    now = datetime.now(pytz.timezone('Europe/Paris'))

    def test_clean_spaces(self):
        words = ["!raid", " ", "egg5", "arena", "@20h00"]
        self.assertEqual(raid.clean_empty_parts(words), ["!raid", "egg5", "arena", "@20h00"])

    def test_fix_lone_at_sign(self):
        words = ["!raid", " ", "egg5", "arena", "@", "20h00"]
        self.assertEqual(raid.fix_lone_at_sign(words), ["!raid", " ", "egg5", "arena", "@20h00"])

    def test_fix_lone_exclamation_sign(self):
        words = ["!", "raid", " ", "egg5", "arena", "@20h00"]
        self.assertEqual(raid.fix_lone_exclamation_sign(words), ["!raid", " ", "egg5", "arena", "@20h00"])

    def test_clean_raid_command(self):
        words = ["!", "raid", "", "egg5", "arena", "@", "20h00"]
        self.assertEqual(raid.clean_raid_command(words), ["!raid", "egg5", "arena", "@20h00"])

    def test_raid_at_time(self):
        hour = "@20h00"
        self.assertEqual(raid.get_raid_hours(hour, 45, now), (time(20, 0), time(20, 45)))
        hour = "@9h12"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (time(9, 12), time(9, 22)))

    def test_raid_end_time(self):
        hour = "20h45"
        self.assertEqual(raid.get_raid_hours(hour, 45, now), (time(20, 0), time(20, 45)))
        hour = "9h22"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (time(9, 12), time(9, 22)))

    def test_format_date_minutes(self):
        minutes = "43"
        self.assertEqual(raid.try_parsing_date(minutes).time(), time(0, 43))
        minutes = "43mn"
        self.assertEqual(raid.try_parsing_date(minutes).time(), time(0, 43))
        minutes = "43min"
        self.assertEqual(raid.try_parsing_date(minutes).time(), time(0, 43))
        minutes = "43minutes"
        self.assertEqual(raid.try_parsing_date(minutes).time(), time(0, 43))
        minutes = "-10"
        self.assertEqual(raid.try_parsing_date(minutes), None)
        minutes = "70"  # TODO: Should work for events
        self.assertEqual(raid.try_parsing_date(minutes), None)

    def test_format_date_hour(self):
        hours = "10h11"
        self.assertEqual(raid.try_parsing_date(hours).time(), time(10, 11))
        hours = "@10h11"
        self.assertEqual(raid.try_parsing_date(hours).time(), time(10, 11))
