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


"""Facets tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from invenio_search.api import Query
from werkzeug.datastructures import MultiDict

from invenio_records_rest.facets import _aggregations, _create_filter_dsl, \
    _post_filter, _query_filter, default_facets_factory, terms_filter


def test_terms_filter():
    """Test terms filter."""
    f = terms_filter("test")
    assert f(['a', 'b']) == dict(terms={'test': ['a', 'b']})


def test_create_filter_dsl():
    """Test request value extraction."""
    app = Flask('testapp')
    kwargs = MultiDict([('a', '1')])
    defs = dict(
        type=terms_filter('type.type'),
        subtype=terms_filter('type.subtype'),
    )

    with app.test_request_context("?type=a&type=b&subtype=c"):
        query, args = _create_filter_dsl(kwargs, defs)
        assert len(query['bool']['filter']) == 2
        assert args == MultiDict([
            ('a', '1'),
            ('type', 'a'),
            ('type', 'b'),
            ('subtype', 'c')
        ])

    kwargs = MultiDict([('a', '1')])
    with app.test_request_context("?atype=a&atype=b"):
        query, args = _create_filter_dsl(kwargs, defs)
        assert query is None
        assert args == kwargs


def test_post_filter(app, user_factory):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter('type'),
        subtype=terms_filter('subtype'),
    )

    with app.test_request_context("?type=test"):
        q = Query("value")
        query, args = _post_filter(q, urlargs, defs)
        assert 'post_filter' in query.body
        assert query.body['post_filter'] == dict(
            bool=dict(
                filter=[dict(terms=dict(type=['test']))]
            ),
        )
        assert args['type'] == 'test'

    with app.test_request_context("?anotertype=test"):
        q = Query("value")
        query, args = _post_filter(q, urlargs, defs)
        assert 'post_filter' not in query.body


def test_query_filter(app, user_factory):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter('type'),
        subtype=terms_filter('subtype'),
    )

    with app.test_request_context("?type=test"):
        q = Query("value")
        body = q.body['query']
        query, args = _query_filter(q, urlargs, defs)
        assert 'post_filter' not in query.body
        assert query.body['query']['filtered']['query'] == body
        assert query.body['query']['filtered']['filter'] == \
            dict(
                bool=dict(
                    filter=[dict(terms=dict(type=['test']))]
                ),
            )
        assert args['type'] == 'test'

    with app.test_request_context("?anotertype=test"):
        q = Query("value")
        body = q.body['query']
        query, args = _query_filter(q, urlargs, defs)
        assert query.body['query'] == body


def test_aggregations(app, user_factory):
    """Test aggregations."""
    with app.test_request_context(""):
        q = Query("value")
        defs = dict(
            type=dict(
                terms=dict(field="upload_type"),
            ),
            subtype=dict(
                terms=dict(field="subtype"),
            )
        )
        assert _aggregations(q, defs).body['aggs'] == defs


def test_default_facets_factory(app, user_factory):
    """Test aggregations."""
    defs = dict(
        aggs=dict(
            type=dict(
                terms=dict(field="upload_type"),
            ),
            subtype=dict(
                terms=dict(field="subtype"),
            )
        ),
        filters=dict(
            subtype=terms_filter('subtype'),
        ),
        post_filters=dict(
            type=terms_filter('type'),
        ),
    )
    app.config['RECORDS_REST_FACETS']['testidx'] = defs

    with app.test_request_context("?type=a&subtype=b"):
        q = Query("value")
        query, urlkwargs = default_facets_factory(q, 'testidx')
        assert query.body['aggs'] == defs['aggs']
        assert 'post_filter' in query.body
        assert 'filtered' in query.body['query']

        q = Query("value")
        query, urlkwargs = default_facets_factory(q, 'anotheridx')
        assert 'aggs' not in query.body
        assert 'post_filter' not in query.body
        assert 'filtered' not in query.body['query']
