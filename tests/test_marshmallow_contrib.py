# SPDX-FileCopyrightText: 2019 CERN.
# SPDX-License-Identifier: MIT
"""Invenio marshmallow contrib tests."""

from invenio_records_rest.schemas.fields.marshmallow_contrib import _get_func_args


def test_get_func_args_on_func():
    def test_function(arg1, arg2, arg3=None, arg4=None):
        pass

    expected_args = ["arg1", "arg2", "arg3", "arg4"]
    assert _get_func_args(test_function) == expected_args


def test_get_func_args_on_method():
    class test_class:
        def test_method(self, arg1, arg2, arg3):
            pass

    expected_args = ["self", "arg1", "arg2", "arg3"]
    assert _get_func_args(test_class().test_method) == expected_args


def test_get_func_args_on_callable():
    class test_callable:
        def __call__(self, arg1, arg2, arg3):
            pass

    expected_args = ["self", "arg1", "arg2", "arg3"]
    assert _get_func_args(test_callable) == expected_args
