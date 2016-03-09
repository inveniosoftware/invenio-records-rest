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

"""Search tests."""

from __future__ import absolute_import, print_function

import copy
import json

import pytest
from flask import url_for
from helpers import control_num, create_record, subtest_self_link, test_data, \
    test_data2, test_data3, test_data4
from invenio_db import db
from invenio_search import current_search_client
from six.moves.urllib.parse import parse_qs, urlparse

from invenio_records_rest.facets import terms_filter


def test_valid_search(app, user_factory):
    """Test VALID record search request (GET .../records/?q=...)."""
    with app.app_context():
        # create the record using the internal API
        pid1, record1 = create_record(test_data)
        pid2, record2 = create_record(test_data2)
        pid3, record3 = create_record(test_data3)
        pid4, record4 = create_record(test_data4)

        with user_factory('allowed') as allowed_user, \
                user_factory('forbidden') as forbidden_user:
            # create one user allowed to delete the record
            allowed_user.read_access(True, str(record1.id))
            allowed_user.read_access(True, str(record2.id))
            allowed_user.read_access(True, str(record3.id))
            allowed_user.read_access(True, str(record4.id))
            allowed_login = allowed_user.login_function()
            # create one user who is not allowed to delete the record
            forbidden_user.read_access(False, str(record1.id))
            forbidden_user.read_access(False, str(record2.id))
            forbidden_user.read_access(False, str(record3.id))
            forbidden_user.read_access(False, str(record4.id))
            forbidden_login = forbidden_user.login_function()
            db.session.commit()

        es_index = app.config["RECORDS_REST_DEFAULT_SEARCH_INDEX"]
        current_search_client.indices.flush(wait_if_ongoing=True,
                                            force=True,
                                            index=es_index)

        with app.test_client() as client:
            forbidden_login(client)
            headers = [('Accept', 'application/json')]
            res = client.get(url_for('invenio_records_rest.recid_list',
                                     q='back'),
                             headers=headers)
            assert res.status_code == 200
            data = json.loads(res.get_data(as_text=True))
            assert isinstance(data['hits']['hits'], list)
            assert len(data['hits']['hits']) == 0

        with app.test_client() as client:
            allowed_login(client)
            headers = [('Accept', 'application/json')]
            res = client.get(url_for('invenio_records_rest.recid_list',
                                     q='back', sort='-year'),
                             headers=headers)
            assert res.status_code == 200
            data = json.loads(res.get_data(as_text=True))
            assert isinstance(data['hits']['hits'], list)
            assert data['hits']['total'] == 2

            subtest_expected_hits(data['hits']['hits'], [
                (pid2.pid_value, control_num(test_data2, 2)),
                (pid1.pid_value, control_num(test_data, 1)),
            ], client)

        # test pagination
        with app.test_client() as client:
            allowed_login(client)
            headers = [('Accept', 'application/json')]
            res = client.get(url_for('invenio_records_rest.recid_list',
                                     q='the', page='1', size='2', sort='year'),
                             headers=headers)
            assert res.status_code == 200
            data = json.loads(res.get_data(as_text=True))
            assert isinstance(data['hits']['hits'], list)
            assert data['hits']['total'] == 3

            subtest_expected_hits(data['hits']['hits'], [
                (pid3.pid_value, control_num(test_data3, 3)),
                (pid1.pid_value, control_num(test_data, 1)),
            ], client)
            assert 'next' in data['links'].keys()
            assert 'prev' not in data['links'].keys()

            # check next page
            url = external_to_relative_url(data['links']['next'])
            res2 = client.get(url)
            assert res2.status_code == 200
            data2 = json.loads(res2.get_data(as_text=True))
            assert isinstance(data2['hits']['hits'], list)
            assert data2['hits']['total'] == 3

            subtest_expected_hits(data2['hits']['hits'], [
                (pid2.pid_value, control_num(test_data2, 2)),
            ], client)
            assert 'next' not in data2['links'].keys()
            assert 'prev' in data2['links'].keys()

            # check previous page
            url = external_to_relative_url(data2['links']['prev'])
            res3 = client.get(url)
            assert res3.status_code == 200
            # check that the previous link returns the same response
            data3 = json.loads(res3.get_data(as_text=True))
            data3_copy = copy.deepcopy(data3)
            data3_copy['links'] = {
                k: normalise_url(v) for k, v in data3_copy['links'].items()
            }
            data_copy = copy.deepcopy(data)
            data_copy['links'] = {
                k: normalise_url(v) for k, v in data_copy['links'].items()
            }
            assert data3_copy == data_copy


def test_invalid_search(app, user_factory):
    """Test INVALID record search request (GET .../records/?q=...)."""
    with app.app_context():
        with user_factory('allowed') as allowed_user:
            allowed_login = allowed_user.login_function()
            db.session.commit()

        with app.test_client() as client:
            allowed_login(client)
            # test not supported accept type
            headers = [('Accept', 'application/does_not_exist')]
            res = client.get(url_for('invenio_records_rest.recid_list',
                                     q='back'),
                             headers=headers)
            assert res.status_code == 406


def test_invalid_search_query_syntax(app, user_factory):
    """Test INVALID record search request (GET .../records/?q=...)."""
    with app.app_context():
        with app.test_client() as client:
            # test not supported accept type
            headers = [('Accept', 'application/json')]
            res = client.get(
                url_for('invenio_records_rest.recid_list', q='+title:bad',
                        _external=False),
                headers=headers)
            assert res.status_code == 400
            body = json.loads(res.get_data(as_text=True))
            assert 'message' in body
            assert body['status'] == 400


def test_max_result_window(app, user_factory):
    """Test INVALID record search request (GET .../records/?q=...)."""
    with app.app_context():
        url = url_for('invenio_records_rest.recid_list',
                      page='500', size='20', _external=False)
    with app.test_client() as client:
        res = client.get(url)
        assert res.status_code == 400
        body = json.loads(res.get_data(as_text=True))
        assert 'message' in body
        assert body['status'] == 400


def test_search_default_aggregation_serialization(app, user_factory):
    """Test the elasticsearch aggregations without custom formatter."""
    subtest_search_aggregation_serialization(app, user_factory, {
        'stars': {
            'buckets': [
                {'key': 4, 'doc_count': 2},
                {'key': 3, 'doc_count': 1}
            ],
            'sum_other_doc_count': 0,
            'doc_count_error_upper_bound': 0,
        },
    })


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
            }
        },
        'RECORDS_REST_FACETS': {
            'invenio_records_rest_test_index': {
                'aggs': {
                    'stars': {'terms': {'field': 'stars'}}
                },
                'post_filters': {
                    'type': terms_filter('type'),
                }
            }
        },
    }
})], indirect=['app'])
def test_search_custom_aggregation_serialization(app, user_factory):
    """Test the elasticsearch aggregations with a custom formatter."""
    subtest_search_aggregation_serialization(app, user_factory, {
        'stars': {
            'buckets': [
                {'key': 4, 'doc_count': 2},
                {'key': 3, 'doc_count': 1}
            ],
            'sum_other_doc_count': 0,
            'doc_count_error_upper_bound': 0,
        },
    })


def subtest_search_aggregation_serialization(app, user_factory, expected):
    """Test the serialization of elasticsearch aggregations."""
    with app.app_context():
        # create the record using the internal API
        pid1, record1 = create_record(test_data)
        pid2, record2 = create_record(test_data2)
        pid3, record3 = create_record(test_data3)

        with user_factory('allowed') as allowed_user:
            # create one user allowed to delete the record
            allowed_user.read_access(True, str(record1.id))
            allowed_user.read_access(True, str(record2.id))
            allowed_user.read_access(True, str(record3.id))
            allowed_login = allowed_user.login_function()
        db.session.commit()

        es_index = app.config["RECORDS_REST_DEFAULT_SEARCH_INDEX"]
        current_search_client.indices.flush(wait_if_ongoing=True,
                                            force=True,
                                            index=es_index)

        def aggregation_query_enhancer(query, **kwargs):
            """Enhance query with an aggregation."""
            query.body['aggs'] = {'stars': {'terms': {'field': 'stars'}}}

        enhancers = app.config.get('SEARCH_QUERY_ENHANCERS', [])
        enhancers.append(aggregation_query_enhancer)
        app.config.update(
            SEARCH_QUERY_ENHANCERS=enhancers,
        )

        with app.test_client() as client:
            allowed_login(client)
            headers = [('Accept', 'application/json')]
            res = client.get(url_for('invenio_records_rest.recid_list',
                                     q='the', sort='year'),
                             headers=headers)
            assert res.status_code == 200
            data = json.loads(res.get_data(as_text=True))
            assert isinstance(data['hits']['hits'], list)
            assert data['hits']['total'] == 3

            subtest_expected_hits(data['hits']['hits'], [
                (pid3.pid_value, control_num(test_data3, 3)),
                (pid1.pid_value, control_num(test_data, 1)),
                (pid2.pid_value, control_num(test_data2, 2)),
            ], client)
            assert data['aggregations'] == expected


def external_to_relative_url(url):
    """Build relative URL from external URL.

    This is needed because the test client discards query parameters on
    external urls.
    """
    parsed = urlparse(url)
    return parsed.path + '?' + '&'.join([
        '{0}={1}'.format(param, val[0]) for
        param, val in parse_qs(parsed.query).items()
    ])


def normalise_url(url):
    """Build a comparable dict from the given url.

    The resulting dict can be comparend even when url's query parameters
    are in a different order.
    """
    parsed = urlparse(url)
    return {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'qs': parse_qs(parsed.query),
    }


def subtest_expected_hits(hits, expected, client):
    """Check that returned search hits are as expected."""
    assert len(hits) == len(expected)
    for idx in range(len(hits)):
        record_data = hits[idx]
        expected_id = expected[idx][0]
        expected_data = expected[idx][1]
        # check that the returned self link returns the same data
        subtest_self_link(record_data, None, client)
        assert str(record_data['id']) == expected_id
        assert record_data['metadata'] == expected_data
