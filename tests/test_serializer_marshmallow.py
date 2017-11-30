# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.base import PreprocessorMixin
from invenio_records_rest.serializers.marshmallow import MarshmallowMixin


class SimpleMarshmallowSerializer(MarshmallowMixin, PreprocessorMixin):
    """Simple Marshmallow serializer."""


class TestSchema(Schema):
    title = fields.Str(attribute='metadata.title')
    author = fields.Function(lambda metadata, context: context['author'])


def test_transform_record():
    """Test marshmallow serializer."""
    serializer = SimpleMarshmallowSerializer(TestSchema)
    data = serializer.transform_record(
        PersistentIdentifier(pid_type='recid', pid_value='1'),
        Record({'title': 'test'}),
        marshmallow_context=dict(author='test2')
    )
    assert data == dict(title='test', author='test2')


def test_transform_search_hit():
    """Test marshmallow serializer."""
    serializer = SimpleMarshmallowSerializer(TestSchema)
    data = serializer.transform_record(
        PersistentIdentifier(pid_type='recid', pid_value='1'),
        Record({'title': 'test'}),
        marshmallow_context=dict(author='test2')
    )
    assert data == dict(title='test', author='test2')


def test_transform_record_default_schema():
    """Test marshmallow serializer without providing a schema."""
    serializer = SimpleMarshmallowSerializer()
    data = serializer.transform_record(
        PersistentIdentifier(pid_type='recid', pid_value='1'),
        Record({'title': 'test'})
    )
    assert data == {
        'id': 1,
        'created': None,
        'links': {},
        'metadata': {'title': 'test'},
        'updated': None
    }
