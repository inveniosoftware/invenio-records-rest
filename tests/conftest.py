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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
from contextlib import contextmanager

import pytest
from access_records import filter_record_access_query_enhancer, \
    prepare_indexing
from flask import Flask, url_for
from flask_cli import FlaskCLI
from flask_login import LoginManager
from flask_menu import Menu
from flask_security.utils import encrypt_password
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB, db
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.resolver import Resolver
from invenio_records import InvenioRecords
from invenio_records.api import Record
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, RecordsSearch, current_search_client
from invenio_search.api import DefaultFilter
from permissions import records_create_all, records_delete_all, \
    records_read_all, records_update_all
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_records_rest import InvenioRecordsREST, config

ES_INDEX = 'invenio_records_rest_test_index'


class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""
        index = ES_INDEX
        doc_types = None
        default_filter = DefaultFilter(filter_record_access_query_enhancer)

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'exclude': ['_access']}})


@pytest.yield_fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        TESTING=True,
        SERVER_NAME='localhost:5000',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        RECORDS_REST_ENDPOINTS=config.RECORDS_REST_ENDPOINTS,
        # No permission checking
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_SEARCH_INDEX=ES_INDEX,
        RECORDS_REST_SORT_OPTIONS={
            ES_INDEX: dict(
                year=dict(
                    fields=['year'],
                )
            )
        },
    )
    app.config['RECORDS_REST_ENDPOINTS']['recid']['search_class'] = TestSearch

    # update the application with the configuration provided by the test
    if hasattr(request, 'param') and 'config' in request.param:
        app.config.update(**request.param['config'])

    FlaskCLI(app)
    InvenioDB(app)
    InvenioREST(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    InvenioSearch(app)
    InvenioAccess(app)
    InvenioRecordsREST(app)

    with app.app_context():
        # Setup app
        if not database_exists(str(db.engine.url)) and \
           app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
            create_database(db.engine.url)
        db.drop_all()
        db.create_all()
        if current_search_client.indices.exists(ES_INDEX):
            current_search_client.indices.delete(ES_INDEX)
            current_search_client.indices.create(ES_INDEX)
        prepare_indexing(app)

    with app.app_context():
        # Yield app in request context
        with app.test_request_context():
            yield app

    with app.app_context():
        # Teardown app
        db.drop_all()
        if app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
            drop_database(db.engine.url)
        shutil.rmtree(instance_path)


@pytest.fixture()
def accounts(app):
    """Accounts."""
    app.config.update(
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='CHANGEME',
        SECURITY_PASSWORD_SALT='CHANGEME',
        # conftest switches off permission checking, so re-enable it for this
        # app.
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY='permissions:create_permission_factory',  # noqa
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY='permissions:read_permission_factory',  # noqa
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY='permissions:update_permission_factory',  # noqa
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY='permissions:delete_permission_factory',  # noqa
    )
    # FIXME: use OAuth authentication instead of UI authentication
    Menu(app)
    accounts = InvenioAccounts(app)
    app.register_blueprint(accounts_blueprint)
    InvenioAccess(app)
    return accounts


@pytest.yield_fixture
def default_permissions(app):
    """Test default deny all permission."""
    for key in ['RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY']:
        app.config[key] = getattr(config, key)
    LoginManager(app)
    yield app
    app.extensions['invenio-records-rest'].reset_permission_factories()


@pytest.yield_fixture
def user_factory(app, accounts):
    """Create a user which has all permissions on every records."""
    password = '123456'

    with app.test_request_context():
        login_url = url_for('security.login')

    @contextmanager
    def create_user(name):
        """Create a user.

        Should be called in application context.
        """
        class UserConfig(object):
            def __init__(self, name):
                self.email = '{}@invenio-software.org'.format(name)
                self.user = accounts.datastore.create_user(
                    email=self.email,
                    password=encrypt_password(password),
                    active=True,
                )

            def login_function(self):
                def login(client):
                    res = client.post(login_url, data={
                        'email': self.email, 'password': password})
                    assert res.status_code == 302
                return login

            def create_access(self, allow, record_id=None):
                db.session.add(ActionUsers(
                    action=records_create_all.value, argument=record_id,
                    user=self.user, exclude=not allow))

            def read_access(self, allow, record_id=None):
                db.session.add(ActionUsers(
                    action=records_read_all.value, argument=record_id,
                    user=self.user, exclude=not allow))

            def update_access(self, allow, record_id=None):
                db.session.add(ActionUsers(
                    action=records_update_all.value, argument=record_id,
                    user=self.user, exclude=not allow))

            def delete_access(self, allow, record_id=None):
                db.session.add(ActionUsers(
                    action=records_delete_all.value, argument=record_id,
                    user=self.user, exclude=not allow))

        yield UserConfig(name)

    yield create_user


@pytest.fixture(scope='session')
def resolver():
    """Create a persistent identifier resolver."""
    return Resolver(pid_type='recid', object_type='rec',
                    getter=Record.get_record)
