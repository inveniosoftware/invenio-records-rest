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

"""Test query factories."""

from __future__ import absolute_import, print_function

import pytest

from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_records_rest.query import default_query_factory, es_query_factory


def test_default_query_factory(app, user_factory):
    """Test default query factory."""
    app.config.update(dict(SEARCH_QUERY_ENHANCERS=[]))
    with app.test_request_context("?q=test"):
        query, urlargs = default_query_factory('myindex', 1, 10)
        assert query.body['query'] == dict(
            multi_match=dict(
                fields=['_all'],
                query='test',
            ))
        assert query.body['from'] == 0
        assert query.body['size'] == 10
        assert urlargs['q'] == 'test'

    with app.test_request_context("?q=:"):
        pytest.raises(
            InvalidQueryRESTError,
            default_query_factory, 'myindex', 1, 10)


def test_es_query_factory(app, user_factory):
    """Test es query factory."""
    app.config.update(dict(SEARCH_QUERY_ENHANCERS=[]))
    with app.test_request_context("?q=test"):
        query, urlargs = es_query_factory('myindex', 2, 20)
        assert query.body['query'] == dict(
            query_string=dict(
                query="test",
                allow_leading_wildcard=False,
            )
        )
        assert query.body['from'] == 20
        assert query.body['size'] == 20
        assert urlargs['q'] == 'test'

    with app.test_request_context("?q="):
        query, urlargs = es_query_factory('myindex', 2, 20)
        assert query.body['query'] == dict(match_all={})
        assert query.body['from'] == 20
        assert query.body['size'] == 20
        assert urlargs['q'] == ''
