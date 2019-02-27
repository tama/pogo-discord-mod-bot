import unittest

from mod_bot import main


class TestGymNameFinder(unittest.TestCase):

    def test_load_gym(self):
        self.assertEqual(len(main.load_gyms(1, "./test")), 11)