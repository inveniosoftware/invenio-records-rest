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

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Range
from flask import current_app, request
from invenio_rest.errors import FieldError, RESTValidationError
from werkzeug.datastructures import MultiDict


def terms_filter(field):
    """Create a term filter."""
    def inner(values):
        return Q('terms', **{field: values})
    return inner


def range_filter(field, start_date_math=None, end_date_math=None, **kwargs):
    """Create a range filter."""
    def inner(values):
        if len(values) != 1 or values[0].count('--') != 1 or values[0] == '--':
            raise RESTValidationError(
                errors=[FieldError(field, 'Invalid range format.')])

        range_ends = values[0].split('--')
        range_args = dict()

        ineq_opers = [{'strict': 'gt', 'nonstrict': 'gte'},
                      {'strict': 'lt', 'nonstrict': 'lte'}]
        date_maths = [start_date_math, end_date_math]

        # Add the proper values to the dict
        for (range_end, strict, opers,
             date_math) in zip(range_ends, ['>', '<'], ineq_opers, date_maths):

            if range_end != '':
                # If first char is '>' for start or '<' for end
                if range_end[0] == strict:
                    dict_key = opers['strict']
                    range_end = range_end[1:]
                else:
                    dict_key = opers['nonstrict']

                if date_math:
                    range_end = '{0}||{1}'.format(range_end, date_math)

                range_args[dict_key] = range_end

        args = kwargs.copy()
        args.update(range_args)

        return Range(**{field: args})

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

    return (filters, urlkwargs)


def _post_filter(search, urlkwargs, definitions):
    """Ingest post filter in query."""
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.post_filter(filter_)

    return (search, urlkwargs)


def _query_filter(search, urlkwargs, definitions):
    """Ingest query filter in query."""
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.filter(filter_)

    return (search, urlkwargs)


def _aggregations(search, definitions):
    """Add aggregations to query."""
    if definitions:
        for name, agg in definitions.items():
            search.aggs[name] = agg
    return search


def default_facets_factory(search, index):
    """Add facets to query."""
    urlkwargs = MultiDict()

    facets = current_app.config['RECORDS_REST_FACETS'].get(index)

    if facets is not None:
        # Aggregations.
        search = _aggregations(search, facets.get("aggs", {}))

        # Query filter
        search, urlkwargs = _query_filter(
            search, urlkwargs, facets.get("filters", {}))

        # Post filter
        search, urlkwargs = _post_filter(
            search, urlkwargs, facets.get("post_filters", {}))

    return (search, urlkwargs)
