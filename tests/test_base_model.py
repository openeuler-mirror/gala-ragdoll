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
"""
Description: unit tests for ragdoll/app/models/base_model_.py
"""
import unittest

from ragdoll.app.models.base_model_ import Model


class NestedModel(Model):
    """A nested model used to exercise the to_dict recursion branches."""

    swagger_types = {"value": int}
    attribute_map = {"value": "value"}

    def __init__(self, value=None):
        self.value = value


class SimpleModel(Model):
    """A model mixing plain, nested, list and dict fields."""

    swagger_types = {
        "name": str,
        "age": int,
        "nested": NestedModel,
        "items": list,
        "mapping": dict,
    }
    attribute_map = {
        "name": "name",
        "age": "age",
        "nested": "nested",
        "items": "items",
        "mapping": "mapping",
    }

    def __init__(self, name=None, age=None, nested=None, items=None, mapping=None):
        self.name = name
        self.age = age
        self.nested = nested
        self.items = items
        self.mapping = mapping


class TestModelBase(unittest.TestCase):
    """Tests for the Model base class in base_model_.py."""

    def test_to_dict_plain_values(self):
        """Plain (non-container) values are copied unchanged."""
        model = SimpleModel(name="aops", age=1)
        result = model.to_dict()
        self.assertEqual(result.get("name"), "aops")
        self.assertEqual(result.get("age"), 1)

    def test_to_dict_nested_model(self):
        """A nested model value is serialized via its own to_dict."""
        model = SimpleModel(name="aops", nested=NestedModel(value=7))
        result = model.to_dict()
        self.assertEqual(result.get("nested"), {"value": 7})

    def test_to_dict_list_of_models(self):
        """A list of models is serialized element by element."""
        model = SimpleModel(items=[NestedModel(1), NestedModel(2)])
        result = model.to_dict()
        self.assertEqual(result.get("items"), [{"value": 1}, {"value": 2}])

    def test_to_dict_list_of_plain(self):
        """A list of plain values keeps its elements unchanged."""
        model = SimpleModel(items=[1, 2, 3])
        result = model.to_dict()
        self.assertEqual(result.get("items"), [1, 2, 3])

    def test_to_dict_dict_of_models(self):
        """A dict whose values are models is serialized per value."""
        model = SimpleModel(mapping={"a": NestedModel(9)})
        result = model.to_dict()
        self.assertEqual(result.get("mapping"), {"a": {"value": 9}})

    def test_to_dict_dict_of_plain(self):
        """A dict whose values are plain keeps its values unchanged."""
        model = SimpleModel(mapping={"a": 1})
        result = model.to_dict()
        self.assertEqual(result.get("mapping"), {"a": 1})

    def test_to_dict_empty_model(self):
        """A model without swagger_types serializes to an empty dict."""
        self.assertEqual(Model().to_dict(), {})

    def test_to_str(self):
        """to_str returns a printable string of the serialized dict."""
        model = SimpleModel(name="aops", age=1)
        self.assertIsInstance(model.to_str(), str)
        self.assertIn("aops", model.to_str())

    def test_repr_equals_to_str(self):
        """__repr__ delegates to to_str."""
        model = SimpleModel(name="aops")
        self.assertEqual(repr(model), model.to_str())

    def test_eq_and_ne(self):
        """__eq__ compares the whole instance state; __ne__ is its negation."""
        first = SimpleModel(name="aops", age=1)
        second = SimpleModel(name="aops", age=1)
        third = SimpleModel(name="other", age=2)
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_from_dict(self):
        """from_dict builds an instance and fills fields present in the data."""
        result = SimpleModel.from_dict({"name": "aops", "age": 3})
        self.assertIsInstance(result, SimpleModel)
        self.assertEqual(result.name, "aops")
        self.assertEqual(result.age, 3)

    def test_from_dict_without_swagger_types(self):
        """When swagger_types is empty the raw data is returned unchanged."""
        self.assertEqual(Model.from_dict({"raw": 1}), {"raw": 1})


if __name__ == "__main__":
    unittest.main()
