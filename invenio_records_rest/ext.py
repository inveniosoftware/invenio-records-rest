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

from werkzeug.utils import cached_property, import_string

from . import config
from .views import create_blueprint


class _RecordRESTState(object):
    """Record REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app
        self._read_permission_factory = None
        self._create_permission_factory = None
        self._update_permission_factory = None
        self._delete_permission_factory = None
        self._search_index = None
        self._search_type = None

    @cached_property
    def read_permission_factory(self):
        """Load default read permission factory."""
        if self._read_permission_factory is None:
            imp = self.app.config.get(
                'RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY')
            self._read_permission_factory = import_string(imp) if imp else None
        return self._read_permission_factory

    @cached_property
    def create_permission_factory(self):
        """Load default create permission factory."""
        if self._create_permission_factory is None:
            imp = self.app.config.get(
                'RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY')
            self._create_permission_factory = import_string(imp) \
                if imp else None
        return self._create_permission_factory

    @cached_property
    def update_permission_factory(self):
        """Load default update permission factory."""
        if self._update_permission_factory is None:
            imp = self.app.config.get(
                'RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY')
            self._update_permission_factory = import_string(imp) \
                if imp else None
        return self._update_permission_factory

    @cached_property
    def delete_permission_factory(self):
        """Load default delete permission factory."""
        if self._delete_permission_factory is None:
            imp = self.app.config.get(
                'RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY')
            self._delete_permission_factory = import_string(imp) \
                if imp else None
        return self._delete_permission_factory


class InvenioRecordsREST(object):
    """Invenio-Records-REST extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        # Register records API blueprints
        app.register_blueprint(
            create_blueprint(app.config['RECORDS_REST_ENDPOINTS'])
        )
        app.extensions['invenio-records-rest'] = _RecordRESTState(app)

    def init_config(self, app):
        """Initialize configuration."""
        # Set up API endpoints for records.
        for k in dir(config):
            if k.startswith('RECORDS_REST_'):
                app.config.setdefault(k, getattr(config, k))
