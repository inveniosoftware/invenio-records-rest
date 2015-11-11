# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

from flask import jsonify, url_for


def record_self_link(pid, record, **kwargs):
    """Create self link to a given record.

    :Parameters:
        - `record` (Record): record to which the generated link will point.
        - `**kwargs`: additional parameters given to flask.url_for.
    :Returns: link pointing to the given record.
    :Returns Type: str
    """
    return url_for(
        "invenio_records_rest.{0}_item".format(pid.pid_type),
        pid_value=pid.pid_value, **kwargs)


def record_to_json_serializer(pid, record, code=200, headers=None):
    """Build a json flask response using the given record.

    :Returns: A flask response with json data.
    :Returns Type: :py:class:`flask.Response`
    """
    # FIXME: use a formatter instead once it is implemented
    self_link = record_self_link(pid, record, _external=True)
    response = jsonify({
        'id': pid.pid_value,
        'metadata': record,
        'links': {
            'self': self_link
        },
        # FIXME: ISO8601 encoded timestamps in UTC
        'created': record.model.created,
        'updated': record.model.updated,
        'revision': record.model.version_id,
    })
    response.status_code = code
    if headers is not None:
        response.headers.extend(headers)
    response.headers['location'] = self_link
    response.set_etag(str(record.model.version_id))
    return response
