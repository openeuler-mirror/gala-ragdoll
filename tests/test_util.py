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
Description: unit tests for util.py
"""
import unittest
import datetime

from ragdoll.app.util import (
    deserialize_date,
    deserialize_datetime,
    deserialize_model,
)

DATE_STR = "2024-01-15"
DATETIME_STR = "2024-01-15T10:30:00"


class MockSwaggerModel:
    """Mock model class with swagger_types for testing."""
    swagger_types = {"name": str, "value": int}
    attribute_map = {"name": "name", "value": "value"}

    def __init__(self):
        self.name = None
        self.value = None


class TestUtil(unittest.TestCase):
    """Tests for util.py deserialization functions."""

    def test_deserialize_date(self):
        """Test deserialize_date parses date string."""
        result = deserialize_date(DATE_STR)
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_deserialize_datetime(self):
        """Test deserialize_datetime parses datetime string."""
        result = deserialize_datetime(DATETIME_STR)
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.year, 2024)

    def test_deserialize_model(self):
        """Test deserialize_model fills model from dict."""
        data = {"name": "test", "value": 42}
        result = deserialize_model(data, MockSwaggerModel)
        self.assertEqual(result.name, "test")
        self.assertEqual(result.value, 42)

    def test_deserialize_model_empty_data(self):
        """Test deserialize_model with empty dict."""
        result = deserialize_model({}, MockSwaggerModel)
        self.assertIsNone(result.name)
        self.assertIsNone(result.value)

    def test_deserialize_model_none_data(self):
        """Test deserialize_model with None data."""
        result = deserialize_model(None, MockSwaggerModel)
        self.assertIsNone(result.name)


if __name__ == "__main__":
    unittest.main()
