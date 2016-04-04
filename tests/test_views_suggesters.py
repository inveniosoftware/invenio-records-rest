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


"""Basic tests."""

from __future__ import absolute_import, print_function

import json
from time import sleep

import pytest
from flask import url_for
from helpers import create_record, test_data
from invenio_db import db
from invenio_indexer.api import RecordIndexer


@pytest.mark.parametrize('app', [({
    'config': {
        'RECORDS_REST_ENDPOINTS': {
            'recid': {
                'pid_type': 'recid',
                'pid_minter': 'recid',
                'pid_fetcher': 'recid',
                'search_class': 'conftest:TestSearch',
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
                'suggesters': {
                    'suggest_title': {
                        'completion': {
                            'field': 'suggest_title'
                        }
                    },
                    'suggest_byyear': {
                        'completion': {
                            'field': 'suggest_byyear',
                            'context': 'year'
                        }
                    }
                }
            }
        }
    }
})], indirect=['app'])
def test_valid_suggest(app):
    """Test VALID record creation request (POST .../records/)."""
    pid, record = create_record(test_data)
    db.session.commit()
    indexer = RecordIndexer()
    indexer.index_by_id(record.id)
    sleep(3)

    with app.test_client() as client:
        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'application/json')]
        res = client.get(
            url_for(
                'invenio_records_rest.recid_suggest', suggest_title="Back"),
            headers=headers
        )
        assert res.status_code == 200

        # check that the returned record matches the given data
        response_data = json.loads(res.get_data(as_text=True))

        assert len(response_data['suggest_title']) == 1

        title = response_data['suggest_title'][0]['options'][0]['text']
        # note that recid ingests the control_number.
        assert title == record['title']
