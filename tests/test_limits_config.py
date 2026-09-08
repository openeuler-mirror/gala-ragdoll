import unittest

from ragdoll.app.config_model.limits_config import LimitsConfig


class TestLimitsConfig(unittest.TestCase):

    def setUp(self):
        self.config = LimitsConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "*\tsoft\tnofile\t65535"
        error, result = LimitsConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ["*", "soft", "nofile", "65535"])

    def test_parse_multiple_lines(self):
        conf = "* soft nofile 65535\nroot hard nofile 102400"
        error, result = LimitsConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 2)

    def test_parse_skips_comments_and_empty(self):
        conf = "# comment\n\n* soft nofile 65535\n"
        error, result = LimitsConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 1)

    def test_parse_error_wrong_domain(self):
        conf = "invalid soft nofile 65535"
        error, result = LimitsConfig.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_error_wrong_type(self):
        conf = "* invalid nofile 65535"
        error, result = LimitsConfig.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_error_wrong_item(self):
        conf = "* soft invalid 65535"
        error, result = LimitsConfig.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_empty(self):
        error, result = LimitsConfig.parse_conf_to_dict("")
        self.assertFalse(error)
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_write_roundtrip(self):
        conf = "*\tsoft\tnofile\t65535"
        self.config.read_conf(conf)
        self.assertEqual(len(self.config.conf), 1)
        written = self.config.write_conf()
        self.assertIn("*", written)
        self.assertIn("soft", written)
        self.assertIn("nofile", written)


if __name__ == "__main__":
    unittest.main()
