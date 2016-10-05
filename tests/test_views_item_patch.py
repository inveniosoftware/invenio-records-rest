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

"""Patch tests."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from helpers import _mock_validate_fail, get_json, record_url


@pytest.mark.parametrize('content_type', [
    'application/json-patch+json', 'application/json-patch+json;charset=utf-8'
])
def test_valid_patch(app, test_records, test_patch, content_type):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]
    pid, record = test_records[0]

    # Check that
    assert record.patch(test_patch)

    with app.test_client() as client:
        # Check that patch and record is not the same value for year.
        url = record_url(pid)
        previous_year = get_json(client.get(url))['metadata']['year']

        # Patch record
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 200

        # Check that year changed.
        assert previous_year != get_json(client.get(url))['metadata']['year']


@pytest.mark.parametrize('content_type', [
    'application/json-patch+json', 'application/json-patch+json;charset=utf-8'
])
def test_patch_deleted(app, test_records, test_patch, content_type):
    """Test patching deleted record."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]
    pid, record = test_records[0]

    with app.test_client() as client:
        # Delete record.
        url = record_url(pid)
        assert client.delete(url).status_code == 204

        # check patch response for deleted resource
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 410


@pytest.mark.parametrize('charset', [
    '', ';charset=utf-8'
])
def test_invalid_patch(app, test_records, test_patch, charset):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type',
         'application/json-patch+json{0}'.format(charset))
    ]
    pid, record = test_records[0]

    with app.test_client() as client:
        url = record_url(pid)

        # Non-existing record
        res = client.patch(
            record_url('0'), data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 404

        # Invalid accept mime type.
        headers = [('Content-Type',
                    'application/json-patch+json{0}'.format(charset)),
                   ('Accept', 'video/mp4')]
        res = client.patch(url, data=json.dumps(test_patch), headers=headers)
        assert res.status_code == 406

        # Invalid content type
        headers = [('Content-Type', 'video/mp4{0}'.format(charset)),
                   ('Accept', 'application/json')]
        res = client.patch(url, data=json.dumps(test_patch), headers=headers)
        assert res.status_code == 415

        # Invalid Patch
        res = client.patch(
            url,
            data=json.dumps([{'invalid': 'json-patch{0}'.format(charset)}]),
            headers=HEADERS)
        assert res.status_code == 400

        # Invalid JSON
        res = client.patch(url, data='{', headers=HEADERS)
        assert res.status_code == 400

        # Invalid ETag
        res = client.patch(
            url,
            data=json.dumps(test_patch),
            headers={
                'Content-Type': 'application/json-patch+json{0}'.format(
                    charset),
                'If-Match': '"2"'
            }
        )
        assert res.status_code == 412


@mock.patch('invenio_records.api.Record.validate', _mock_validate_fail)
@pytest.mark.parametrize('content_type', [
    'application/json-patch+json', 'application/json-patch+json;charset=utf-8'
])
def test_validation_error(app, test_records, test_patch, content_type):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]
    pid, record = test_records[0]

    # Check that
    assert record.patch(test_patch)

    with app.test_client() as client:
        # Check that patch and record is not the same value for year.
        url = record_url(pid)
        previous_year = get_json(client.get(url))['metadata']['year']

        # Patch record
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 400
