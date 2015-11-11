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

import uuid
from functools import wraps

from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request, url_for
from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError, PIDRedirectedError, PIDUnregistered
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.decorators import require_content_types
from jsonpatch import JsonPatchException, JsonPointerException
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.routing import BuildError

from .serializers import record_to_json_serializer


def create_blueprint(endpoints):
    """Create Invenio-Records-REST blueprint."""
    blueprint = Blueprint(
        'invenio_records_rest',
        __name__,
        url_prefix='',
    )

    for endpoint, options in (endpoints or {}).items():
        for rule in create_url_rules(endpoint, **options):
            blueprint.add_url_rule(**rule)

    return blueprint


def create_url_rules(endpoint, list_route=None, item_route=None,
                     pid_type=None, pid_minter=None):
    """Create Werkzeug URL rules."""
    assert list_route
    assert item_route
    assert pid_type

    resolver = Resolver(pid_type=pid_type, object_type='rec',
                        getter=Record.get_record)

    serializers = {'application/json': record_to_json_serializer, }

    list_view = RecordsListResource.as_view(
        RecordsListResource.view_name.format(endpoint),
        resolver=resolver,
        minter_name=pid_minter,
        serializers=serializers)
    item_view = RecordResource.as_view(
        RecordResource.view_name.format(endpoint),
        resolver=resolver,
        serializers=serializers)

    return [
        dict(rule=list_route, view_func=list_view),
        dict(rule=item_route, view_func=item_view),
    ]


def pass_record(f):
    """Decorator to retrieve persistent identifier and record."""
    @wraps(f)
    def inner(self, pid_value, *args, **kwargs):
        try:
            pid, record = self.resolver.resolve(pid_value)
        except (PIDDoesNotExistError, PIDUnregistered):
            abort(404)
        except PIDDeletedError:
            abort(410)
        except PIDMissingObjectError as e:
            current_app.logger.exception(
                "No object assigned to {0}.".format(e.pid),
                extra={'pid': e.pid})
            abort(500)
        except PIDRedirectedError as e:
            try:
                location = url_for(
                    'invenio_records_rest.{0}_item'.format(
                        e.destination_pid.pid_type),
                    pid_value=e.destination_pid.pid_value)
                data = dict(
                    status=301,
                    message="Moved Permanently",
                    location=location,
                )
                response = make_response(jsonify(data), data['status'])
                response.headers['Location'] = location
                return response
            except BuildError:
                current_app.logger.exception(
                    "Invalid redirect - pid_type '{0}' "
                    "endpoint missing.".format(
                        e.destination_pid.pid_type),
                    extra={
                        'pid': e.pid,
                        'destination_pid': e.destination_pid,
                    })
                abort(500)

        return f(self, pid, record, *args, **kwargs)
    return inner


class RecordsListResource(ContentNegotiatedMethodView):
    """Resource for records listing."""

    view_name = '{0}_list'

    def __init__(self, resolver=None, minter_name=None, **kwargs):
        """Constructor."""
        super(RecordsListResource, self).__init__(**kwargs)
        self.resolver = resolver
        self.minter = current_pidstore.minters[minter_name]

    def post(self, **kwargs):
        """Create a record.

        :returns: The created record.
        """
        if request.content_type != 'application/json':
            abort(415)

        # TODO: accept non json content (MARC21...)
        data = request.get_json()
        if data is None:
            return abort(400)

        try:
            # Create uuid for record
            record_uuid = uuid.uuid4()
            # Create persistent identifier
            pid = self.minter(record_uuid, data=data)
            # Create record
            record = Record.create(data, id_=record_uuid)

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Failed to create record.")
            abort(500)
        return self.make_response(pid, record, 201)


class RecordResource(ContentNegotiatedMethodView):
    """Resource for record items."""

    view_name = '{0}_item'

    def __init__(self, resolver=None, **kwargs):
        """Constructor.

        :param resolver: Persistent identifier resolver instance.
        """
        super(RecordResource, self).__init__(**kwargs)
        self.resolver = resolver

    @pass_record
    def get(self, pid, record, **kwargs):
        """Get a record.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The requested record.
        """
        self.check_etag(str(record.model.version_id))
        return pid, record

    @require_content_types('application/json-patch+json')
    @pass_record
    def patch(self, pid, record, **kwargs):
        """Modify a record.

        The data should be a JSON-patch, which will be applied to the record.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The modified record.
        """
        # TODO: accept 'application/json' mediatype and use the object
        # to replace the specified attributes
        data = request.get_json(force=True)
        if data is None:
            abort(400)

        self.check_etag(str(record.model.version_id))
        try:
            record = record.patch(data)
        except (JsonPatchException, JsonPointerException):
            abort(400)

        record.commit()
        db.session.commit()
        return pid, record

    @require_content_types('application/json')
    @pass_record
    def put(self, pid, record, **kwargs):
        """Replace a record.

        The body should be a JSON object, which will fully replace the current
        record metadata.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The modified record.
        """
        # TODO: accept non json content (MARC21...)
        data = request.get_json()
        if data is None:
            abort(400)
        self.check_etag(str(record.model.version_id))
        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()
        return self.make_response(pid, record)
