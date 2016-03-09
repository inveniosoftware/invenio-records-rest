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

"""Test sorter."""

from __future__ import absolute_import, print_function

import json

import pytest
from flask import url_for


def test_options_view(app, user_factory):
    """Test default sorter factory."""
    app.config["RECORDS_REST_SORT_OPTIONS"] = dict(
        invenio_records_rest_test_index=dict(
            myfield=dict(
                fields=['field1:asc'],
                title='My Field',
                order=2,
            ),
            anotherfield=dict(
                fields=['field2:asc'],
                title='My Field',
                default_order='desc',
                order=1,
            )
        )
    )

    with app.app_context():
        with app.test_client() as client:
            res = client.get(
                url_for('invenio_records_rest.recid_list_options'))
            data = json.loads(res.get_data(as_text=True))
            assert data['max_result_window'] == 10000
            assert data['default_media_type'] == 'application/json'
            assert data['item_media_types'] == ['application/json']
            assert data['search_media_types'] == ['application/json']
            assert data['sort_fields'] == [
                {'anotherfield': {
                    'title': 'My Field',
                    'default_order': 'desc'
                }},
                {'myfield': {
                    'title': 'My Field',
                    'default_order': 'asc'
                }}
            ]


@pytest.mark.parametrize('app', [({
    'config': {
        'RECORDS_REST_ENDPOINTS': {
            'recid': {
                'pid_type': 'recid',
                'pid_minter': 'recid',
                'pid_fetcher': 'recid',
                'search_index': 'invenio_records_rest_test_index',
                'search_type': 'record',
                'record_serializers': {
                    'application/json': 'invenio_records_rest.serializers'
                    ':json_v1_response',
                },
                'search_serializers': {
                    'application/json': 'invenio_records_rest.serializers'
                    ':json_v1_search'
                },
                'list_route': '/records/',
                'item_route': '/records/<pid_value>',
                'use_options_view': False,
            }
        }
    }
})], indirect=['app'])
def test_use_options(app, user_factory):
    """Test extension initialization."""
    with app.app_context():
        with app.test_client() as client:
            res = client.get('/records/_options')
            assert res.status_code == 404
