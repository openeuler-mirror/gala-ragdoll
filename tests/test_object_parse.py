# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2022. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
# pylint: disable=protected-access
"""
Description: unit tests for ragdoll/app/utils/object_parse.py
"""
import json
import sys
import unittest
from unittest import mock

try:  # libyang is a C extension that may be absent; stub only when unavailable
    import libyang  # noqa: F401  # pylint: disable=unused-import
except ImportError:
    sys.modules["libyang"] = mock.MagicMock()

from ragdoll.app.utils.object_parse import ObjectParse  # noqa: E402


def make_parser():
    """Build an ObjectParse without running YangModule() in __init__."""
    return ObjectParse.__new__(ObjectParse)


class TestParseModelToJson(unittest.TestCase):
    """Tests for parse_model_to_json."""

    def test_serializes_conf_dict(self):
        parser = make_parser()
        d_model = mock.Mock()
        d_model.conf = {"a": 1, "b": "x"}
        result = parser.parse_model_to_json(d_model)
        self.assertEqual(json.loads(result), {"a": 1, "b": "x"})

    def test_result_is_indented_json_string(self):
        parser = make_parser()
        d_model = mock.Mock()
        d_model.conf = {"a": 1}
        result = parser.parse_model_to_json(d_model)
        self.assertIsInstance(result, str)
        self.assertIn("\n", result)


class TestCreateConfModelByType(unittest.TestCase):
    """Tests for create_conf_model_by_type fallback branch."""

    def test_unknown_type_returns_empty_string(self):
        parser = make_parser()
        result = parser.create_conf_model_by_type("definitely_not_a_real_type")
        self.assertEqual(result, "")


class TestGetConfTypeByConfPath(unittest.TestCase):
    """Tests for get_conf_type_by_conf_path no-model branch."""

    def test_returns_empty_when_no_yang_model(self):
        parser = make_parser()
        parser._yang_modules = mock.Mock()
        parser._yang_modules.getModuleByFilePath.return_value = None
        self.assertEqual(parser.get_conf_type_by_conf_path("/no/such/path"), "")


class TestParseEarlyReturns(unittest.TestCase):
    """The parse_* methods return '' when the conf type cannot be resolved."""

    def setUp(self):
        self.parser = make_parser()
        self.parser._yang_modules = mock.Mock()
        self.parser._yang_modules.getModuleByFilePath.return_value = None

    def test_parse_conf_to_json(self):
        self.assertEqual(self.parser.parse_conf_to_json("/no/such/path", "content"), "")

    def test_parse_dir_conf_to_json(self):
        self.assertEqual(self.parser.parse_dir_conf_to_json("/no/such/path", []), "")

    def test_parse_directory_single_conf_to_json(self):
        self.assertEqual(self.parser.parse_directory_single_conf_to_json("content", "/no/such/path"), "")


if __name__ == "__main__":
    unittest.main()
