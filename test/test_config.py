import unittest
import os
from mod_bot.conf import read_config, load_guilds_config, get, set_key


class TestConfigCRUD(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_path = os.path.dirname(os.path.abspath(__file__)) + "/test_config.json"
        cls.gid = "573519479334633472"
        cls.filePath = "/tmp/bot/data/"
        cls.dirPath = cls.filePath + cls.gid + "/"
        if os.path.exists(cls.dirPath + 'config.json'):
            os.remove(cls.dirPath + "config.json")
            os.rmdir(cls.dirPath)

        os.makedirs(os.path.dirname(cls.dirPath))
        with open(cls.filePath + cls.gid + "/config.json", 'w+') as f:
            f.write("""{ "raid_duration" : 30}""")

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.dirPath + "config.json")
        os.rmdir(cls.dirPath)

    def test_read_config(self):
        conf = read_config(self.config_path)
        self.assertEqual(45, conf["raid_duration"])
        self.assertEqual("PBL", conf["listen_to"][self.gid]["id"])

    def test_load_guilds_config(self):
        conf = read_config(self.config_path)
        load_guilds_config(conf)
        self.assertEqual(30, conf["listen_to"][self.gid]["conf"]["raid_duration"])

    def test_get(self):
        conf = read_config(self.config_path)
        load_guilds_config(conf)
        self.assertEqual(45, get(None, "raid_duration", conf))
        self.assertEqual(30, get(self.gid, "raid_duration", conf))
        self.assertEqual(5, get(self.gid, "delete_interval_after_warning", conf))

    def test_set_key(self):
        conf = read_config(self.config_path)

        # Cannot change global conf
        with self.assertRaises(FileNotFoundError):
            set_key("toto", conf, None, 20)

        set_key("toto", conf, self.gid, 20)
        self.assertEqual(20, get(self.gid, "toto", conf), "Can set a new variable in gid conf")

        #  Cannot set a new var in an unknown gid
        with self.assertRaises(FileNotFoundError):
            set_key("toto", conf, "test_gid", 20)

        set_key("toto", conf, self.gid, 25)
        self.assertEqual(25, get(self.gid, "toto", conf), "Can modify variable in gid conf")


