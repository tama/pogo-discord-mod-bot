import unittest

from mod_bot import raid
from datetime import time
from datetime import datetime
from datetime import timedelta
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
        hour = "@9:12"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (time(9, 12), time(9, 22)))

    def test_raid_end_time(self):
        hour = "20h45"
        self.assertEqual(raid.get_raid_hours(hour, 45, now), (time(20, 0), time(20, 45)))
        hour = "9h22"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (time(9, 12), time(9, 22)))
        hour = "9:22"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (time(9, 12), time(9, 22)))
        hour = "42"
        end_time = (now + timedelta(minutes=42)).time()
        start_time = (now + timedelta(minutes=32)).time()
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (start_time, end_time), "no suffix")
        hour = "42mn"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (start_time, end_time), "mn")
        hour = "42min"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (start_time, end_time), "min")
        hour = "42minutes"
        self.assertEqual(raid.get_raid_hours(hour, 10, now), (start_time, end_time), "minutes")

    def test_format_date_hour(self):
        hours = "10h11"
        self.assertEqual(raid.try_parsing_date(hours)[0].time(), time(10, 11))
        self.assertEqual(raid.try_parsing_date(hours)[1], False)
        hours = "10:11"
        self.assertEqual(raid.try_parsing_date(hours)[0].time(), time(10, 11))
        self.assertEqual(raid.try_parsing_date(hours)[1], False)
        hours = "@10h11"
        self.assertEqual(raid.try_parsing_date(hours)[0].time(), time(10, 11))
        self.assertEqual(raid.try_parsing_date(hours)[1], True)
        hours = "@10:11"
        self.assertEqual(raid.try_parsing_date(hours)[0].time(), time(10, 11))
        self.assertEqual(raid.try_parsing_date(hours)[1], True)

    def test_parse_minutes(self):
        minutes = "42"
        self.assertEqual(raid.parse_minutes(minutes), 42)
        minutes = "42mn"
        self.assertEqual(raid.parse_minutes(minutes), 42)
        minutes = "42min"
        self.assertEqual(raid.parse_minutes(minutes), 42)
        minutes = "42minutes"
        self.assertEqual(raid.parse_minutes(minutes), 42)
        minutes = "-10"
        self.assertEqual(raid.parse_minutes(minutes), None)
        minutes = "70"
        self.assertEqual(raid.parse_minutes(minutes), 70)
