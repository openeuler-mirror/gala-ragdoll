# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
Description: unit tests for format.py
"""
import unittest

from ragdoll.app.utils.format import Format

DOMAIN_VALID = "test_domain"
DOMAIN_INVALID = ""
OBJ_NAME = "domain"
OP_NAME = "sync"
SUCC_LIST = ["domain1", "domain2"]
FAIL_LIST = ["domain3"]


class TestFormatDomainCheck(unittest.TestCase):
    """Tests for Format.domainCheck static method."""

    def test_valid_domain(self):
        """Test domainCheck returns True for valid domain."""
        self.assertTrue(Format.domainCheck(DOMAIN_VALID))

    def test_empty_domain(self):
        """Test domainCheck returns False for empty string."""
        self.assertFalse(Format.domainCheck(DOMAIN_INVALID))

    def test_special_chars_domain(self):
        """Test domainCheck returns False for special characters."""
        self.assertFalse(Format.domainCheck("test domain"))

    def test_long_domain(self):
        """Test domainCheck returns False for domain > 255 chars."""
        long_domain = "a" * 256
        self.assertFalse(Format.domainCheck(long_domain))


class TestFormatSplice(unittest.TestCase):
    """Tests for Format splice string methods."""

    def test_splice_all_succ_string(self):
        """Test spliceAllSuccString formats success message."""
        result = Format.spliceAllSuccString(OBJ_NAME, OP_NAME, SUCC_LIST)
        self.assertIn(str(len(SUCC_LIST)), result)
        self.assertIn(OP_NAME, result)

    def test_splice_error_string_with_fails(self):
        """Test splicErrorString with both success and failure."""
        result = Format.splicErrorString(OBJ_NAME, OP_NAME, SUCC_LIST, FAIL_LIST)
        self.assertIn(str(len(SUCC_LIST)), result)
        self.assertIn(str(len(FAIL_LIST)), result)

    def test_splice_error_string_no_fails(self):
        """Test splicErrorString with no failures."""
        result = Format.splicErrorString(OBJ_NAME, OP_NAME, SUCC_LIST, [])
        self.assertIn(str(len(SUCC_LIST)), result)


class TestFormatPathJoin(unittest.TestCase):
    """Tests for Format.two_abs_join static method."""

    def test_join_paths(self):
        """Test two_abs_join joins two absolute paths."""
        result = Format.two_abs_join("/home/user", "/etc/hosts")
        self.assertIn("etc", result)
        self.assertIn("hosts", result)


class TestFormatRsplit(unittest.TestCase):
    """Tests for Format.rsplit static method."""

    def test_rsplit_with_sep(self):
        """Test rsplit splits from right."""
        result = Format.rsplit("a.b.c", ".")
        self.assertEqual(result, "c")

    def test_rsplit_no_match(self):
        """Test rsplit returns original string when sep not found."""
        result = Format.rsplit("abc", ".")
        self.assertEqual(result, "abc")


class TestFormatArchSep(unittest.TestCase):
    """Tests for Format.arch_sep static method."""

    def test_arch_sep_x86(self):
        """Test arch_sep extracts x86_64 architecture."""
        result = Format.arch_sep("package-1.0-1.x86_64.rpm")
        self.assertIn("x86_64", result)


if __name__ == "__main__":
    unittest.main()
