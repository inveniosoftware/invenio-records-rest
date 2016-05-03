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

"""Implementention of various utility functions."""

from functools import partial

import six
from flask import abort, current_app, jsonify, make_response, request, url_for
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError, PIDRedirectedError, PIDUnregistered
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from werkzeug.routing import BaseConverter, BuildError
from werkzeug.utils import import_string


def obj_or_import_string(value, default=None):
    """Import string or return object."""
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default


def load_or_import_from_config(key, app=None, default=None):
    """Load or import value from config."""
    app = app or current_app
    imp = app.config.get(key)
    return obj_or_import_string(imp, default=default)


def allow_all(*args, **kwargs):
    """Return permission that always allow an access."""
    return type('Allow', (), {'can': lambda self: True})()


def deny_all(*args, **kwargs):
    """Return permission that always deny an access."""
    return type('Deny', (), {'can': lambda self: False})()


def check_elasticsearch(record, *args, **kwargs):
    """Return permission that check if the record exists in ES index."""
    def can(self):
        """Try to search for given record."""
        search = request._methodview.search_class()
        search = search.get_record(str(record.id))
        return search.count() == 1

    return type('CheckES', (), {'can': can})()


class PIDConverter(BaseConverter):
    """Resolve PID value."""

    def __init__(self, url_map, pid_type, getter=None, record_class=None):
        """Initialize PID resolver."""
        super(PIDConverter, self).__init__(url_map)
        getter = obj_or_import_string(getter, default=partial(
            obj_or_import_string(record_class, default=Record).get_record,
            with_deleted=True
        ))
        self.resolver = Resolver(pid_type=pid_type, object_type='rec',
                                 getter=getter)

    def to_python(self, value):
        """Resolve PID value."""
        try:
            return self.resolver.resolve(value)
        except (PIDDoesNotExistError, PIDUnregistered):
            abort(404)
        except PIDDeletedError:
            abort(410)
        except PIDMissingObjectError as e:
            current_app.logger.exception(
                'No object assigned to {0}.'.format(e.pid),
                extra={'pid': e.pid})
            abort(500)
        except PIDRedirectedError as e:
            try:
                prefix = ''
                for rule in self.map.iter_rules():
                    if '.' in rule.endpoint:
                        prefix = rule.endpoint.split('.')[0] + '.'
                        break

                location = url_for(
                    '{0}{1}_item'.format(prefix, e.destination_pid.pid_type),
                    pid_value=e.destination_pid.pid_value)
                data = dict(
                    status=301,
                    message='Moved Permanently',
                    location=location,
                )
                response = make_response(jsonify(data), data['status'])
                response.headers['Location'] = location
                return abort(response)
            except BuildError:
                current_app.logger.exception(
                    'Invalid redirect - pid_type "{0}" '
                    'endpoint missing.'.format(
                        e.destination_pid.pid_type),
                    extra={
                        'pid': e.pid,
                        'destination_pid': e.destination_pid,
                    })
                abort(500)
