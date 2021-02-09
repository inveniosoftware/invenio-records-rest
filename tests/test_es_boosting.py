# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""ElasticSearch boosting tests."""

from __future__ import absolute_import, print_function

import pytest
from helpers import get_json


@pytest.mark.parametrize('app', [dict(
    endpoint=dict(
        search_factory_imp='invenio_records_rest.query.es_search_factory'
    )
)], indirect=['app'])
def test_boosted_query(app, indexed_records, search_url):
    """Test query with boosted abstract field."""
    with app.test_client() as client:
        res = client.get(search_url, query_string=dict(q='guide'))
        assert len(get_json(res)['hits']['hits']) == 2
        # the first result should be the one that has the word 'guide' in its
        # title because the title field is boosted
        first_result = get_json(res)['hits']['hits'][0]
        assert first_result['metadata']['title'] == "A Guide"
