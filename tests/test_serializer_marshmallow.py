# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2026 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_rest.serializer import BaseSchema as Schema
from marshmallow import fields
from marshmallow_utils.context import context_schema

from invenio_records_rest.serializers.base import PreprocessorMixin
from invenio_records_rest.serializers.marshmallow import MarshmallowMixin


class SimpleMarshmallowSerializer(MarshmallowMixin, PreprocessorMixin):
    """Simple Marshmallow serializer."""


class _TestSchema(Schema):
    title = fields.Str(attribute="metadata.title")
    author = fields.Function(lambda *args, **kwargs: context_schema.get()["author"])


def test_transform_record():
    """Test marshmallow serializer."""
    serializer = SimpleMarshmallowSerializer(_TestSchema)
    data = serializer.transform_record(
        PersistentIdentifier(pid_type="recid", pid_value="1"),
        Record({"title": "test"}),
        marshmallow_context=dict(author="test2"),
    )
    assert data == dict(title="test", author="test2")


def test_transform_search_hit():
    """Test marshmallow serializer."""
    serializer = SimpleMarshmallowSerializer(_TestSchema)
    data = serializer.transform_record(
        PersistentIdentifier(pid_type="recid", pid_value="1"),
        Record({"title": "test"}),
        marshmallow_context=dict(author="test2"),
    )
    assert data == dict(title="test", author="test2")


def test_transform_record_default_schema():
    """Test marshmallow serializer without providing a schema."""
    serializer = SimpleMarshmallowSerializer()
    data = serializer.transform_record(
        PersistentIdentifier(pid_type="recid", pid_value="1"), Record({"title": "test"})
    )
    assert data == {
        "id": "1",
        "created": None,
        "links": {},
        "metadata": {"title": "test"},
        "updated": None,
    }
