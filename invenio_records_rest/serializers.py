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

"""REST API resources."""

from __future__ import absolute_import, print_function

import pytz
from flask import jsonify, url_for


def record_self_link(pid_value, pid_type, record, **kwargs):
    """Create self link to a given record.

    :param pid_value: pid value.
    :type pid_value: str
    :param pid_type: type of the pid.
    :type pid_type: str
    :param record: record to which the generated link will point.
    :type record: Record
    :param **kwargs: additional parameters given to flask.url_for.
    :Returns: link pointing to the given record.
    :Returns Type: str
    """
    return url_for(
        'invenio_records_rest.{0}_item'.format(pid_type),
        pid_value=pid_value, **kwargs)


def record_to_json_serializer(pid, record, code=200,
                              headers=None):
    """Build a json flask response using the given record.

    :param pid: record's pid.
    :param record: record to which the generated link will point.
    :type record: Record
    :param code: http code of the response.
    :type code: int
    :param header: header to extend for the response.
    :Returns: A flask response with json data.
    :Returns Type: :py:class:`flask.Response`
    """
    # FIXME: use a formatter instead once it is implemented
    self_link = record_self_link(pid.pid_value, pid.pid_type, record,
                                 _external=True)
    formatted_record = {
        'id': pid.pid_value,
        'metadata': record,
        'links': {
            'self': self_link
        },
        # FIXME: ISO8601 encoded timestamps in UTC
        'created': pytz.utc.localize(record.created).isoformat(),
        'updated': pytz.utc.localize(record.updated).isoformat(),
        'revision': record.revision_id,
    }
    response = jsonify(formatted_record)
    response.status_code = code
    if headers is not None:
        response.headers.extend(headers)
    response.headers['location'] = self_link
    response.set_etag(str(record.model.version_id))
    return response


def search_to_json_serializer_factory(hit_formatter,
                                      aggregations_formatter=None):
    """Create a search result to flask response serializers.

    :param hit_formatter: function formatting a single hit. It should return
    a dict.
    :param aggregation_formatter: function formatting aggregations returned
    by invenio_search.
    :Return: a function formatting search results.
    """
    def serializer(pid_fetcher, search_result, links=None,
                   code=200, headers=None):
        """Build a json flask response using the given search result.

        :param pid_fetcher: function extracting pid type and value from a
        import record metadata.
        :param search_result: search result as returned by invenio_search.
        :param code: http code of the response.
        :type code: int
        :param header: header to extend for the response.
        """
        result = {
            'hits': {
                'hits': [hit_formatter(hit, pid_fetcher)
                         for hit in search_result['hits']['hits']],
                'total': search_result['hits']['total'],
            },
            'links': links or {},
        }
        if 'aggregations' in search_result:
            if aggregations_formatter:
                result['aggregations'] = aggregations_formatter(
                    search_result['aggregations'])
            else:
                result['aggregations'] = search_result['aggregations']
        response = jsonify(result)
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)
        return response
    return serializer


def record_hit_formatter(hit, pid_fetcher):
    """Format a single record returned by a search result.

    :param hit: record returned by a search result.
    :param pid_fetcher: function fetching pid from a search hit.
    """
    # retrieve the pid value and pid type of a given hit
    fetched_pid = pid_fetcher(hit['_id'], hit['_source'])
    self_link = record_self_link(fetched_pid.pid_value, fetched_pid.pid_type,
                                 hit['_source'], _external=True)
    data = {
        'id': fetched_pid.pid_value,
        'metadata': hit['_source'],
        'links': {
            'self': self_link
        },
        'revision': hit['_version'],
    }

    for key in ['_created', '_updated']:
        if key in data['metadata']:
            data[key[1:]] = data['metadata'][key]
            del data['metadata'][key]

    return data

search_to_json_serializer = search_to_json_serializer_factory(
    hit_formatter=record_hit_formatter
)
"""Example of search result formatting function."""
