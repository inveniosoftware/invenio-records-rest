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

from flask import Blueprint, abort, jsonify, request, url_for
from invenio_db import db
from invenio_records.api import Record
from invenio_rest import ContentNegotiatedMethodView
from jsonpatch import JsonPatchException, JsonPointerException
from sqlalchemy.orm.exc import NoResultFound

blueprint = Blueprint(
    'invenio_records_rest',
    __name__,
    url_prefix='/records'
)


def record_self_link(record, **kwargs):
    """Create self link to a given record.

    :Parameters:
        - `record` (Record): record to which the generated link will point.
        - `**kwargs`: additional parameters given to flask.url_for.
    :Returns: link pointing to the given record.
    :Returns Type: str
    """
    return url_for('.' + RecordResource.view_name,
                   record_id=record.model.id, **kwargs)


def record_to_json_serializer(record, code=200, headers=None):
    """Build a json flask response using the given record.

    :Returns: A flask response with json data.
    :Returns Type: :py:class:`flask.Response`
    """
    # FIXME: use a formatter instead once it is implemented
    self = record_self_link(record, _external=True)
    response = jsonify({
        'id': record.model.id,
        'data': record,
        'links': {
            'self': self
        }
    })
    response.status_code = code
    if headers is not None:
        response.headers.extend(headers)
    response.headers['location'] = self
    response.set_etag(str(record.model.version_id))
    return response


class RecordsListResource(ContentNegotiatedMethodView):
    """Resource for '/records'."""

    view_name = 'records_list'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(RecordsListResource, self).__init__(*args, **kwargs)
        self.serializers = {
            'application/json': record_to_json_serializer,
        }

    def post(self, **kwargs):
        """Create a Record.

        :Returns: The created record.
        """
        if request.content_type != 'application/json':
            abort(415)
        # TODO: accept non json content (MARC21...)
        data = request.get_json()
        if data is None:
            return abort(400)
        record = Record.create(data, identifier_key=None)
        db.session.commit()
        return self.make_response(record, 201)


class RecordResource(ContentNegotiatedMethodView):
    """Resource for '/records/<int:record_id>'."""

    view_name = 'record_item'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(RecordResource, self).__init__(*args, **kwargs)
        self.serializers = {
            'application/json': record_to_json_serializer,
        }

    def get(self, record_id, **kwargs):
        """Get a Record.

        :Parameters:
            - `record_id`: id of the record to retrieve.
        :Returns: The requested record.
        """
        try:
            record = Record.get_record(record_id)
        except NoResultFound:
            abort(404)

        self.check_etag(str(record.model.version_id))

        return record

    def patch(self, record_id, **kwargs):
        """Modify a Record.

        The data should be a json-patch, which will be applied to the record.

        :Parameters:
            - `record_id` (int): id of the record to retrieve.
        :Returns: Modified record.
        """
        if request.content_type != 'application/json-patch+json':
            abort(415)

        # TODO: accept 'application/json' mediatype and use the object
        # to replace the specified attributes

        data = request.get_json(force=True)
        if data is None:
            abort(400)
        try:
            record = Record.get_record(record_id)
        except NoResultFound:
            abort(404)
        self.check_etag(str(record.model.version_id))
        try:
            record = record.patch(data)
        except (JsonPatchException, JsonPointerException):
            abort(400)
        record.commit()
        db.session.commit()
        return record

    def put(self, record_id, **kwargs):
        """Replace a Record metadata.

        The body should be a json object, which will fully replace the current
        record metadata.

        :Parameters:
            - `record_id` (int): id of the record to retrieve.
        :Returns: Modified record.
        """
        if request.content_type != 'application/json':
            abort(415)
        # TODO: accept non json content (MARC21...)
        data = request.get_json()
        if data is None:
            abort(400)
        try:
            record = Record.get_record(record_id)
        except NoResultFound:
            abort(404)
        self.check_etag(str(record.model.version_id))
        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()
        return self.make_response(record)


blueprint.add_url_rule('/',
                       view_func=RecordsListResource
                       .as_view(RecordsListResource.view_name))
blueprint.add_url_rule('/<int:record_id>',
                       view_func=RecordResource
                       .as_view(RecordResource.view_name))
