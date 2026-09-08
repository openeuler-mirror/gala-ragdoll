import unittest

from ragdoll.app.config_model.text_config import TextConfig


class TestTextConfig(unittest.TestCase):

    def setUp(self):
        self.config = TextConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "line1\nline2\nline3"
        result = TextConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["line1", "line2", "line3"])

    def test_parse_skips_comments_hash(self):
        conf = "# comment\nline1\n"
        result = TextConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["line1"])

    def test_parse_skips_comments_semicolon(self):
        conf = "; comment\nline1\n"
        result = TextConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["line1"])

    def test_parse_skips_empty_lines(self):
        conf = "\n\nline1\n\n\nline2\n"
        result = TextConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["line1", "line2"])

    def test_parse_replaces_tabs(self):
        conf = "col1\tcol2\n"
        result = TextConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["col1 col2"])

    def test_parse_empty(self):
        result = TextConfig.parse_conf_to_dict("")
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_write_roundtrip(self):
        conf = "line1\nline2"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf, ["line1", "line2"])
        written = self.config.write_conf()
        self.assertIn("line1", written)
        self.assertIn("line2", written)

    def test_read_empty_not_stored(self):
        self.config.read_conf("  \n  \n")
        self.assertEqual(self.config.conf, [])

    def test_write_conf_skips_none(self):
        self.config.conf = ["line1", None, "line2"]
        written = self.config.write_conf()
        self.assertIn("line1", written)
        self.assertIn("line2", written)


if __name__ == "__main__":
    unittest.main()
