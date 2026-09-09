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
Description: unit tests for yang_module.py
"""
import unittest
from unittest.mock import patch, MagicMock

from ragdoll.app.utils.yang_module import YangModule

TARGET_DIR = "/tmp/test_yang"
YANG_DIR = "/tmp/test_yang/modules"


class TestYangModuleProperties(unittest.TestCase):
    """Tests for YangModule properties."""

    def test_init(self):
        """Test YangModule initializes correctly."""
        with patch.object(YangModule, "get_yang_path_in_ragdoll", return_value=YANG_DIR):
            module = YangModule()
            self.assertIsNotNone(module)

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_target_dir_property(self, mock_yang_path):
        """Test target_dir property getter and setter."""
        module = YangModule()
        module.target_dir = "/tmp/new"
        self.assertEqual(module.target_dir, "/tmp/new")

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_yang_dir_property(self, mock_yang_path):
        """Test yang_dir property getter and setter."""
        module = YangModule()
        module.yang_dir = YANG_DIR
        self.assertEqual(module.yang_dir, YANG_DIR)

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_module_list_property(self, mock_yang_path):
        """Test module_list property getter and setter."""
        module = YangModule()
        test_list = ["mod1", "mod2"]
        module.module_list = test_list
        self.assertEqual(module.module_list, test_list)

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_ctx_property(self, mock_yang_path):
        """Test ctx property getter and setter."""
        module = YangModule()
        module.ctx = "test_ctx"
        self.assertEqual(module.ctx, "test_ctx")


class TestYangModuleGetXpathInModule(unittest.TestCase):
    """Tests for YangModule.getXpathInModule method."""

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_get_xpath_empty_modules(self, mock_yang_path):
        """Test getXpathInModule with empty modules list."""
        module = YangModule()
        result = module.getXpathInModule([])
        self.assertEqual(result, [])

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_get_xpath_none_modules(self, mock_yang_path):
        """Test getXpathInModule with None modules."""
        module = YangModule()
        result = module.getXpathInModule(None)
        self.assertEqual(result, [])


class TestYangModuleGetModuleByFilePath(unittest.TestCase):
    """Tests for YangModule.getModuleByFilePath method."""

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_get_module_by_file_path_no_modules(self, mock_yang_path):
        """Test getModuleByFilePath returns None when no modules loaded."""
        module = YangModule()
        module.module_list = []
        result = module.getModuleByFilePath("/etc/hosts")
        self.assertIsNone(result)

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_get_module_by_file_path_with_match(self, mock_yang_path):
        """Test getModuleByFilePath returns matching module."""
        module = YangModule()
        mock_mod = MagicMock()
        mock_mod.name.return_value = "hosts"
        module.module_list = [mock_mod]
        result = module.getModuleByFilePath("/etc/hosts")
        self.assertIsNotNone(result)

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_get_module_by_file_path_no_match(self, mock_yang_path):
        """Test getModuleByFilePath returns None when no match."""
        module = YangModule()
        mock_mod = MagicMock()
        mock_mod.name.return_value = "hostname"
        module.module_list = [mock_mod]
        result = module.getModuleByFilePath("/etc/hosts")
        self.assertIsNone(result)


class TestYangModuleCheckYangGrammar(unittest.TestCase):
    """Tests for YangModule.check_yang_grammar method."""

    @patch("ragdoll.app.utils.yang_module.YangModule.get_yang_path_in_ragdoll", return_value=YANG_DIR)
    def test_check_yang_grammar_nonexistent_file(self, mock_yang_path):
        """Test check_yang_grammar returns False for non-existent file."""
        module = YangModule()
        result = module.check_yang_grammar("/nonexistent/file.yang")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
