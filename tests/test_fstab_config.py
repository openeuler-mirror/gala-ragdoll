import unittest

from ragdoll.app.config_model.fstab_config import FstabConfig
from ragdoll.app.constant import FSTAB_COLUMN_NUM


class TestFstabConfig(unittest.TestCase):

    def setUp(self):
        self.config = FstabConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "/dev/sda1 / ext4 defaults 0 1\n/dev/sda2 /home xfs defaults 0 2"
        error, result = FstabConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "/dev/sda1")
        self.assertEqual(result[0][1], "/")
        self.assertEqual(result[0][2], "ext4")

    def test_parse_skips_comments_and_empty(self):
        conf = "# comment\n\n/dev/sda1 / ext4 defaults 0 1\n"
        error, result = FstabConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 1)

    def test_parse_error_wrong_column_count(self):
        conf = "/dev/sda1 / ext4"
        error, result = FstabConfig.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_empty(self):
        error, result = FstabConfig.parse_conf_to_dict("")
        self.assertFalse(error)
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_write_roundtrip(self):
        conf = "/dev/sda1 / ext4 defaults 0 1"
        self.config.read_conf(conf)
        self.assertEqual(len(self.config.conf), 1)
        written = self.config.write_conf()
        self.assertIn("/dev/sda1", written)
        self.assertIn("ext4", written)

    def test_read_error_conf_not_stored(self):
        conf = "/dev/sda1 / ext4"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf, [])


if __name__ == "__main__":
    unittest.main()
