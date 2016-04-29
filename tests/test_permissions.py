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


"""Permissions tests."""

from __future__ import absolute_import, print_function

import json

from helpers import record_url
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_search.api import RecordsSearch

HEADERS = [
    ('Content-Type', 'application/json'),
    ('Accept', 'application/json')
]


def test_valid_create_with_permission2(app, deny_all_permissions,
                                       db, es, es_record, test_data,
                                       search_url):
    """Test valida record create with respect of permissions."""
    with app.test_request_context():
        with app.test_client() as client:
            # Create record
            res = client.post(
                search_url, data=json.dumps(test_data[0]), headers=HEADERS)
            assert res.status_code == 401
            assert len(RecordMetadata.query.all()) == 0
            assert len(PersistentIdentifier.query.all()) == 0
            results = RecordsSearch().query({
                "match_all": {}
            }).execute().to_dict()
            assert len(results['hits']['hits']) == 0


def test_valid_create_with_permission_deny_record(
        app, deny_record_permissions, db, es, es_record, test_data,
        search_url):
    """Test valida record create with respect of permissions.

    Simulate the case of user logged-in but record passed from input is
    malformed.
    """
    with app.test_request_context():
        with app.test_client() as client:
            # Create record
            res = client.post(
                search_url, data=json.dumps(test_data[0]), headers=HEADERS)
            assert res.status_code == 401
            assert len(RecordMetadata.query.all()) == 0
            assert len(PersistentIdentifier.query.all()) == 0
            results = RecordsSearch().query({
                "match_all": {}
            }).execute().to_dict()
            assert len(results['hits']['hits']) == 0


def test_valid_create_deny_login(app, deny_login_permissions,
                                 db, es, es_record, test_data, search_url):
    """Test valida record create with respect of permissions.

    This test simulate a user that is trying to create a record without login
    but with a valid record data.
    """
    with app.test_request_context():
        with app.test_client() as client:
            # Create record
            res = client.post(
                search_url, data=json.dumps(test_data[0]), headers=HEADERS)
            assert res.status_code == 401
            assert len(RecordMetadata.query.all()) == 0
            assert len(PersistentIdentifier.query.all()) == 0
            results = RecordsSearch().query({
                "match_all": {}
            }).execute().to_dict()
            assert len(results['hits']['hits']) == 0


def test_valid_create(app, allow_all_permissions,
                      db, es, es_record, test_data, search_url):
    """Test valida record create with respect of permissions."""
    with app.test_request_context():
        with app.test_client() as client:
            # Create record
            res = client.post(
                search_url, data=json.dumps(test_data[0]), headers=HEADERS)
            assert res.status_code == 201
            assert len(RecordMetadata.query.all()) == 1
            assert len(PersistentIdentifier.query.all()) == 1
            results = RecordsSearch().query({
                "match_all": {}
            }).execute().to_dict()
            assert len(results['hits']['hits']) == 1


def test_default_permissions(app, default_permissions, test_data, search_url,
                             test_records, indexed_records):
    """Test default create permissions."""
    pid, record = test_records[0]
    rec_url = record_url(pid)
    data = json.dumps(test_data[0])
    h = {'Content-Type': 'application/json'}
    hp = {'Content-Type': 'application/json-patch+json'}

    with app.test_client() as client:
        args = dict(data=data, headers=h)
        pargs = dict(data=data, headers=hp)
        qs = {'user': '1'}
        uargs = dict(data=data, headers=h, query_string=qs)
        upargs = dict(data=data, headers=hp, query_string=qs)

        assert client.get(search_url).status_code == 200
        assert client.get(rec_url).status_code == 200

        assert 401 == client.post(search_url, **args).status_code
        assert 405 == client.put(search_url, **args).status_code
        assert 405 == client.patch(search_url).status_code
        assert 405 == client.delete(search_url).status_code

        assert 405 == client.post(rec_url, **args).status_code
        assert 401 == client.put(rec_url, **args).status_code
        assert 401 == client.patch(rec_url, **pargs).status_code
        assert 401 == client.delete(rec_url).status_code

        assert 403 == client.post(search_url, **uargs).status_code
        assert 403 == client.put(rec_url, **uargs).status_code
        assert 403 == client.patch(rec_url, **upargs).status_code
        assert 403 == client.delete(rec_url, query_string=qs).status_code
