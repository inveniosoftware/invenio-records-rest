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

"""Record PUT tests."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from helpers import _mock_validate_fail, get_json, record_url


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_valid_put(app, test_records, content_type):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    pid, record = test_records[0]

    record['year'] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
        assert res.status_code == 200

        # Check that the returned record matches the given data
        assert get_json(res)['metadata']['year'] == 1234

        # Retrieve record via get request
        assert get_json(client.get(url))['metadata']['year'] == 1234


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_valid_put_etag(app, test_records, content_type):
    """Test concurrency control with etags."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    pid, record = test_records[0]

    record['year'] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(
            url,
            data=json.dumps(record.dumps()),
            headers={
                'Content-Type': 'application/json',
                'If-Match': '"{0}"'.format(record.revision_id)
            })
        assert res.status_code == 200

        assert get_json(client.get(url))['metadata']['year'] == 1234


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_put_on_deleted(app, test_records, content_type):
    """Test putting to a deleted record."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    # create the record using the internal API
    pid, record = test_records[0]

    with app.test_client() as client:
        url = record_url(pid)
        assert client.delete(url).status_code == 204

        res = client.put(url, data='{}', headers=HEADERS)
        assert res.status_code == 410


@pytest.mark.parametrize('charset', [
    '', ';charset=utf-8'
])
def test_invalid_put(app, test_records, charset):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type',
         'application/json{0}'.format(charset)),
    ]

    pid, record = test_records[0]

    record['year'] = 1234
    test_data = record.dumps()

    with app.test_client() as client:
        url = record_url(pid)

        # Non-existing record
        res = client.put(
            record_url('0'), data=json.dumps(test_data), headers=HEADERS)
        assert res.status_code == 404

        # Invalid accept mime type.
        headers = [('Content-Type', 'application/json{0}'.format(charset)),
                   ('Accept', 'video/mp4')]
        res = client.put(url, data=json.dumps(test_data), headers=headers)
        assert res.status_code == 406

        # Invalid content type
        headers = [('Content-Type', 'video/mp4{0}'.format(charset)),
                   ('Accept', 'application/json')]
        res = client.put(url, data=json.dumps(test_data), headers=headers)
        assert res.status_code == 415

        # Invalid JSON
        res = client.put(url, data='{invalid-json', headers=HEADERS)
        assert res.status_code == 400

        # Invalid ETag
        res = client.put(
            url,
            data=json.dumps(test_data),
            headers={'Content-Type': 'application/json{0}'.format(charset),
                     'If-Match': '"2"'}
        )
        assert res.status_code == 412


@mock.patch('invenio_records.api.Record.validate', _mock_validate_fail)
@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_validation_error(app, test_records, content_type):
    """Test when record validation fail."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    pid, record = test_records[0]

    record['year'] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
        assert res.status_code == 400
