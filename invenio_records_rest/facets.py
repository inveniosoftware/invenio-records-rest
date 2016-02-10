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

"""Facets factory for REST API."""

from __future__ import absolute_import, print_function

from flask import current_app, request
from werkzeug.datastructures import MultiDict


def terms_filter(field):
    """Create a term filter."""
    def inner(values):
        return {"terms": {field: values}}
    return inner


def _create_filter_dsl(urlkwargs, definitions):
    """Create a filter DSL expression."""
    filters = []
    for name, filter_factory in definitions.items():
        values = request.values.getlist(name, type=str)
        if values:
            filters.append(filter_factory(values))
            for v in values:
                urlkwargs.add(name, v)

    if filters:
        return ({"bool": {"filter": filters}}, urlkwargs)
    return (None, urlkwargs)


def _post_filter(query, urlkwargs, definitions):
    """Ingest post filter in query."""
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    if filters:
        query.body["post_filter"] = filters

    return (query, urlkwargs)


def _query_filter(query, urlkwargs, definitions):
    """Ingest query filter in query."""
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    if filters:
        query.body["query"] = {
            "filtered": {
                "query": query.body["query"],
                "filter": filters,
            }
        }

    return (query, urlkwargs)


def _aggregations(query, definitions):
    """Add aggregations to query."""
    if definitions:
        query.body["aggs"] = definitions
    return query


def default_facets_factory(query, index):
    """Add facets to query."""
    facets = current_app.config['RECORDS_REST_FACETS'].get(index)

    if facets is None:
        return query, {}

    urlkwargs = MultiDict()

    # Aggregations.
    query = _aggregations(query, facets.get("aggs", {}))

    # Query filter
    query, urlkwargs = _query_filter(
        query, urlkwargs, facets.get("filters", {}))

    # Post filter
    query, urlkwargs = _post_filter(
        query, urlkwargs, facets.get("post_filters", {}))

    return (query, urlkwargs)
