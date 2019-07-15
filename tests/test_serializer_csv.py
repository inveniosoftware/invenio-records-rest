# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CSV Core serializer tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.csv import CSVSerializer


class SimpleSchema(Schema):
    """Test schema."""

    titles = fields.Raw(attribute='metadata.titles')
    booklinks = fields.Raw(attribute='metadata.booklinks')
    circulation = fields.Raw(attribute='metadata.circulation')
    books = fields.Raw(attribute='metadata.books')
    document_types = fields.Raw(attribute='metadata.document_types')
    languages = fields.Raw(attribute='metadata.languages')
    keywords = fields.Raw(attribute='metadata.keywords')
    series_objs = fields.Raw(attribute='metadata.series_objs')

    record_1 = {'titles': {"pid": 51, "other": 'A'},
                'languages': ['en', 'fr', 'de'],
                'circulation': {
                    'loans': {
                        'active': 0,
                        'pending': 2
                    },
                    'items': {
                        'pid': 1,
                    }
                },
                'books': [
                    {"author": """Jane's, aka, " Doe""",
                     "pid": 55,
                     "extra": "N/A"},
                    {"author": """John \ \ ", aka.,a,a Doe""",
                     "pid": 56,
                     "extra": "N/A"}
                ],
                'document_types': {
                    'type': {
                        'text': 'STANDARD',
                        'id': 5,
                    },
                },
                'booklinks': [
                    'https://home.cern/physics/dark-matter',
                    'https://home.cern/physics/antimatter'],
                'keywords': {"pid": 1, "text": "a"},
                'series_objs': [
                    {u'pid': u'55', u'volume': u'2'},
                    {u'pid': u'56', u'volume': u'16'},
                    {u'pid': u'52', u'volume': u'98'}],
                }

    record_2 = {'titles': {"pid": 52, "other": 'B'},
                'languages': ['it', 'es'],
                'circulation': {
                    'loans': {
                        'active': 11,
                        'pending': 22
                    },
                    'items': {
                        'pid': 2,
                    }
                },
                'books': [
                    {"author": """Tim ,'aka', ",""",
                     "pid": 65,
                     "extra": "N/A"},
                    {"author": """Jony' ,\", I've\'""",
                     "pid": 66,
                     "extra": "N/A"}
                ],
                'document_types': {
                    'type': {
                        'text': 'PROCEEDINGS',
                        'id': 5,
                    },
                },
                'booklinks': [
                    'https://home.cern/physics/dark-matter',
                    'https://home.cern/physics/antimatter'],
                'keywords': {"pid": 2, "text": "b"},
                'series_objs': [
                    {u'pid': u'75', u'volume': u'68'},
                    {u'pid': u'76', u'volume': u'78'},
                    {u'pid': u'77', u'volume': u'88'}],
                }

    CSV_EXCLUDED_FIELDS = [
        "titles_other",
        "circulation_items",
        "books_0_pid",
        "books_1_pid",
        "books_0_extra",
        "books_1_extra",
        "document_types",
        "booklinks",
        "keywords",
        "series_objs",
    ]


def test_serialize():
    """Test JSON serialize."""

    pid = PersistentIdentifier(pid_type='recid', pid_value='2')
    record = Record(SimpleSchema.record_1)
    data = CSVSerializer(
        SimpleSchema,
        csv_excluded_fields=SimpleSchema.CSV_EXCLUDED_FIELDS).serialize(pid,
                                                                        record)

    assert "books_0_author,books_1_author,circulation_loans_active," \
           "circulation_loans_pending,languages_0,languages_1,languages_2," \
           "titles_pid" in data

    assert """Jane\'s, aka, "" Doe""" in data
    assert """John \\ \\ "", aka.,a,a Doe""" in data


def test_serialize_search():
    """Test CSV serialize."""

    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='doi', pid_value='a')

    data = CSVSerializer(
        SimpleSchema,
        csv_excluded_fields=SimpleSchema.CSV_EXCLUDED_FIELDS).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': SimpleSchema.record_1,
                     '_id': 'a',
                     '_version': 1,
                     },
                    {'_source': SimpleSchema.record_2,
                     '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    )
    assert "books_0_author,books_1_author,circulation_loans_active," \
           "circulation_loans_pending,languages_0,languages_1,languages_2," \
           "titles_pid" in data

    assert """Jane\'s, aka, "" Doe""" in data
    assert """John \\ \\ "", aka.,a,a Doe""" in data
    assert """"Tim ,'aka', "",","Jony' ,"", I've'",11,22,it,es,,52""" in data
