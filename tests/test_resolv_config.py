import unittest

from ragdoll.app.config_model.resolv_config import ResolvConfig


class TestResolvConfig(unittest.TestCase):

    def setUp(self):
        self.config = ResolvConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "nameserver 8.8.8.8\ndomain example.com"
        error, result = ResolvConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"nameserver": "8.8.8.8"})
        self.assertEqual(result[1], {"domain": "example.com"})

    def test_parse_search(self):
        conf = "search example.com corp.example.com"
        error, result = ResolvConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(result[0], {"search": "example.com corp.example.com"})

    def test_parse_skips_comments_and_empty(self):
        conf = "# comment\n\nnameserver 8.8.8.8\n"
        error, result = ResolvConfig.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 1)

    def test_parse_error_invalid_key(self):
        conf = "invalidkey 8.8.8.8"
        error, result = ResolvConfig.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_error_single_field(self):
        conf = "nameserver"
        error, result = ResolvConfig.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_empty(self):
        error, result = ResolvConfig.parse_conf_to_dict("")
        self.assertFalse(error)
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_write_roundtrip(self):
        conf = "nameserver 8.8.8.8\ndomain example.com"
        self.config.read_conf(conf)
        self.assertEqual(len(self.config.conf), 2)
        written = self.config.write_conf()
        self.assertIn("nameserver 8.8.8.8", written)
        self.assertIn("domain example.com", written)


if __name__ == "__main__":
    unittest.main()
