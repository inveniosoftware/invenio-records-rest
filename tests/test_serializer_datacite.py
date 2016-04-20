# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""DataCite serializer tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.datacite import DataCite31Serializer, \
    OAIDataCiteSerializer


class DOISchema(Schema):
    """Test schema."""

    identifierType = fields.Constant('DOI')
    identifier = fields.Raw(attribute='doi')


class SimpleSchema(Schema):
    """Test schema."""

    identifier = fields.Nested(DOISchema, attribute='metadata')


def test_serialize():
    """Test JSON serialize."""
    pid = PersistentIdentifier(pid_type='recid', pid_value='2')
    record = Record({'doi': '10.1234/foo'})
    data = DataCite31Serializer(SimpleSchema).serialize(pid, record)

    assert """<identifier identifierType="DOI">10.1234/foo</identifier>""" \
        in data

    s = DataCite31Serializer(SimpleSchema)
    tree = s.serialize_oaipmh(
        pid, {'_source': record})
    assert len(tree.xpath('/resource/identifier')) == 1

    tree = OAIDataCiteSerializer(v31=s, datacentre='CERN').serialize_oaipmh(
        pid,
        {'_source': record})
    assert len(tree.xpath('/oai_datacite/datacentreSymbol')) == 1


def test_serialize_search():
    """Test JSON serialize."""
    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='doi', pid_value=data['doi'])

    data = DataCite31Serializer(SimpleSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': dict(doi='10.1234/a'), '_id': 'a',
                     '_version': 1},
                    {'_source': dict(doi='10.1234/b'), '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    )
    assert """<identifier identifierType="DOI">10.1234/a</identifier>""" \
        in data
    assert """<identifier identifierType="DOI">10.1234/b</identifier>""" \
        in data

    s = DataCite31Serializer(SimpleSchema)
    tree = s.serialize_oaipmh(
        PersistentIdentifier(pid_type='doi', pid_value='10.1234/b'),
        {'_source': dict(doi='10.1234/b'), '_id': 'b', '_version': 1})
    assert len(tree.xpath('/resource/identifier')) == 1

    tree = OAIDataCiteSerializer(v31=s, datacentre='CERN').serialize_oaipmh(
        PersistentIdentifier(pid_type='doi', pid_value='10.1234/b'),
        {'_source': dict(doi='10.1234/b'), '_id': 'b', '_version': 1})
    assert len(tree.xpath('/oai_datacite/datacentreSymbol')) == 1
