# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Index prefixing tests."""

import json

from conftest import IndexFlusher
from elasticsearch import VERSION as ES_VERSION
from helpers import assert_hits_len, get_json, record_url
from invenio_search import current_search

lt_es7 = ES_VERSION[0] < 7


def test_index_creation(app, prefixed_es):
    """Sanity check for index creation."""
    suffix = current_search.current_suffix
    es_aliases = prefixed_es.indices.get_alias()
    # Keys are the indices
    assert set(es_aliases.keys()) == {
        'test-invenio-records-rest-testrecord{}'.format(suffix),
    }

    aliases = set()
    for index_info in es_aliases.values():
        aliases |= set(index_info.get('aliases', {}).keys())
    assert aliases == {
        'test-invenio-records-rest',
        'test-invenio-records-rest-testrecord',
    }


def test_api_views(app, prefixed_es, db, test_data, search_url, search_class):
    """Test REST API views behavior."""
    suffix = current_search.current_suffix

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json'),
        ]

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        recid = get_json(res)['id']
        assert res.status_code == 201

        # Flush and check indices
        IndexFlusher(search_class).flush_and_wait()
        result = prefixed_es.search(index='test-invenio-records-rest')
        assert len(result['hits']['hits']) == 1
        record_doc = result['hits']['hits'][0]
        assert record_doc['_index'] == \
            'test-invenio-records-rest-testrecord' + suffix
        assert record_doc['_type'] == 'testrecord' if lt_es7 else '_doc'

        # Fetch the record
        assert client.get(record_url(recid)).status_code == 200
        # Record shows up in search
        res = client.get(search_url)
        assert_hits_len(res, 1)

        # Delete the record
        res = client.delete(record_url(recid))
        IndexFlusher(search_class).flush_and_wait()
        result = prefixed_es.search(index='test-invenio-records-rest')
        assert len(result['hits']['hits']) == 0

        # Deleted record should return 410
        assert client.get(record_url(recid)).status_code == 410
        # Record doesn't show up in search
        res = client.get(search_url)
        assert_hits_len(res, 0)
