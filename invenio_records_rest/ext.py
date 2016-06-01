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

"""REST API for invenio-records."""

from __future__ import absolute_import, print_function

from werkzeug.utils import cached_property
import six

from . import config
from .errors import InvalidEndpointConfigError
from .utils import load_or_import_from_config
from .views import create_blueprint
from .config_loader import EndpointConfigSchema
from .proxies import current_records_rest

class _RecordRESTState(object):
    """Record REST state."""

    def __init__(self, app, endpoints):
        """Initialize state."""
        self.app = app
        self.endpoints = endpoints

    @cached_property
    def loaders(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_LOADERS', app=self.app
        )

    @cached_property
    def read_permission_factory(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def create_permission_factory(self):
        """Load default create permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def update_permission_factory(self):
        """Load default update permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def delete_permission_factory(self):
        """Load default delete permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY', app=self.app
        )

    def reset_permission_factories(self):
        """Remove cached permission factories."""
        for key in ('read', 'create', 'update', 'delete'):
            full_key = '{0}_permission_factory'.format(key)
            if full_key in self.__dict__:
                del self.__dict__[full_key]


class InvenioRecordsREST(object):
    """Invenio-Records-REST extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        endpoints = {}
        for endpoint, conf in \
                six.iteritems(app.config['RECORDS_REST_ENDPOINTS']):
            endpoint_config, errors = EndpointConfigSchema().load(conf)
            if errors:
                raise InvalidEndpointConfigError(errors)
            endpoints[endpoint] = endpoint_config

        # Register records API blueprints
        app.register_blueprint(
            create_blueprint(endpoints)
        )
        app.extensions['invenio-records-rest'] = _RecordRESTState(app,
                                                                  endpoints)

    def init_config(self, app):
        """Initialize configuration."""
        # Set up API endpoints for records.
        for k in dir(config):
            if k.startswith('RECORDS_REST_'):
                app.config.setdefault(k, getattr(config, k))
