import unittest

from ragdoll.app.config_model.kv_config import KvConfig


class TestKvConfig(unittest.TestCase):

    def setUp(self):
        self.config = KvConfig()

    # --- parse_conf_to_dict ---

    def test_parse_space_separator(self):
        conf = "key1 value1\nkey2 value2"
        space_type = {"test": ""}
        result = KvConfig.parse_conf_to_dict(conf, space_type, "test")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"key1": "value1"})
        self.assertEqual(result[1], {"key2": "value2"})

    def test_parse_equals_separator(self):
        conf = "key1=value1\nkey2=value2"
        space_type = {"test": "="}
        result = KvConfig.parse_conf_to_dict(conf, space_type, "test")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"key1": "value1"})

    def test_parse_skips_comments_and_empty(self):
        conf = "# comment\n\nkey1 value1\n"
        space_type = {"test": ""}
        result = KvConfig.parse_conf_to_dict(conf, space_type, "test")
        self.assertEqual(len(result), 1)

    def test_parse_space_single_field_returns_empty(self):
        conf = "singlekey"
        space_type = {"test": ""}
        result = KvConfig.parse_conf_to_dict(conf, space_type, "test")
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_conf(self):
        conf = "key1 value1\nkey2 value2"
        space_type = {"test": ""}
        self.config.read_conf(conf, space_type, "test")
        self.assertEqual(len(self.config.conf), 2)

    def test_write_conf_space(self):
        self.config.conf = [{"key1": "value1"}]
        space_type = {"test": ""}
        written = self.config.write_conf(space_type, "test")
        self.assertIn("key1", written)
        self.assertIn("value1", written)

    def test_write_conf_equals(self):
        self.config.conf = [{"key1": "value1"}]
        space_type = {"test": "="}
        written = self.config.write_conf(space_type, "test")
        self.assertIn("key1=value1", written)


if __name__ == "__main__":
    unittest.main()
