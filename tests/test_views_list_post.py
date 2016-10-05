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

"""Record creation."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from helpers import _mock_validate_fail, get_json, record_url
from mock import patch
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_valid_create(app, db, test_data, search_url, content_type):
    """Test VALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]
        HEADERS.append(('Content-Type', content_type))

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 201

        # Check that the returned record matches the given data
        data = get_json(res)
        for k in test_data[0].keys():
            assert data['metadata'][k] == test_data[0][k]

        # Recid has been added in control number
        assert data['metadata']['control_number']

        # Check location header
        assert res.headers['Location'] == data['links']['self']

        # Record can be retrieved.
        assert client.get(record_url(data['id'])).status_code == 200

        # Record can be searched (after a moment of time)
        # Note: Currently we don't index on record creation so this part is
        # disabled.

        # current_search.flush_and_refresh(search_class.Meta.index)
        # res = client.get(
        #     search_url,
        #     query_string={'q': 'control_number:{}'.format(data['id'])})
        # assert_hits_len(res, 1)


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_invalid_create(app, db, test_data, search_url, content_type):
    """Test INVALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]

        # Invalid accept type
        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'video/mp4')]
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=headers)
        assert res.status_code == 406

        # Invalid content-type
        headers = [('Content-Type', 'video/mp4'),
                   ('Accept', 'application/json')]
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=headers)
        assert res.status_code == 415

        # Invalid JSON
        res = client.post(search_url, data='{fdssfd', headers=HEADERS)
        assert res.status_code == 400

        # No data
        res = client.post(search_url, headers=HEADERS)
        assert res.status_code == 400

        # Posting a list instead of dictionary
        pytest.raises(
            TypeError, client.post, search_url, data='[]', headers=HEADERS)

        # Bad internal error:
        with patch('invenio_records_rest.views.db.session.commit') as m:
            m.side_effect = SQLAlchemyError()

            pytest.raises(
                SQLAlchemyError,
                client.post, search_url, data=json.dumps(test_data[0]),
                headers=HEADERS)


@mock.patch('invenio_records.api.Record.validate', _mock_validate_fail)
@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_validation_error(app, db, test_data, search_url, content_type):
    """Test when record validation fail."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 400
