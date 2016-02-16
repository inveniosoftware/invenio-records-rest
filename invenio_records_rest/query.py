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

"""Query factories for REST API."""

from __future__ import absolute_import, print_function

from flask import current_app, request
from invenio_search import Query

from .errors import InvalidQueryRESTError


def default_query_factory(index, page, size):
    """Parse and slice query using Invenio-Query-Parser.

    :param index: Index to search in.
    :param page: Requested page.
    :param size: Request results size.
    :returns: Tuple of (query, URL arguments).
    """
    query_string = request.values.get('q', '')

    try:
        query = Query(query_string)[(page-1)*size:page*size]
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(
                request.values.get('q', '')),
            exc_info=True)
        raise InvalidQueryRESTError()

    return (query, {'q': query_string})


def es_query_factory(index, page, size):
    """Send query directly as query string query to Elasticsearch.

    .. warning:

       All fields in a record that a user can access are searchable! This means
       that if a user can access a record, you cannot include confidential
       information into the record (or you must remove it when indexing).
       Otherwise a user is able to search for the information.

       The reason is that the query string is passed directly to Elasticsearch,
       which takes care of parsing the string.

    :param index: Index to search in.
    :param page: Requested page.
    :param size: Request results size.
    :returns: Tuple of (query, URL arguments).
    """
    query_string = request.values.get('q', '')

    query = Query()
    if query_string.strip():
        query.body['query'] = dict(
            query_string=dict(
                query=query_string,
                allow_leading_wildcard=False,
            )
        )
    query = query[(page-1)*size:page*size]
    return (query, {'q': query_string})
