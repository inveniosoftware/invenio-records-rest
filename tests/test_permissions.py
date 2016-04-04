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


"""Permissions tests."""

from __future__ import absolute_import, print_function

import copy
import json

from flask import url_for
from helpers import create_record, test_data, test_data_patched, test_patch
from invenio_db import db


def test_create_permissions(app, user_factory, resolver):
    """Test create permission."""
    with app.app_context():
        # create users
        with user_factory('allowed') as allowed_user, \
                user_factory('forbidden') as forbidden_user:
            # create one user allowed to create records
            allowed_user.create_access(True)
            allowed_login = allowed_user.login_function()
            # create one user who is not allowed to create records
            forbidden_user.create_access(False)
            forbidden_login = forbidden_user.login_function()
            db.session.commit()

        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'application/json')]
        # test create without being authenticated
        with app.test_client() as client:
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 401
        # test not allowed create
        with app.test_client() as client:
            forbidden_login(client)
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 403
        # test allowed create
        with app.test_client() as client:
            allowed_login(client)
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 201
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            pid, internal_record = resolver.resolve(response_data['id'])
            assert internal_record == response_data['metadata']


def test_read_one_permissions(app, user_factory, resolver):
    """Test read permission."""
    with app.app_context():
        # create the record using the internal API
        pid, internal_record = create_record(test_data)
        with user_factory('allowed') as allowed_user, \
                user_factory('forbidden') as forbidden_user:
            # create one user allowed to read the record
            allowed_user.read_access(True, str(internal_record.id))
            allowed_login = allowed_user.login_function()
            # create one user who is not allowed to read the record
            forbidden_user.read_access(False, str(internal_record.id))
            forbidden_login = forbidden_user.login_function()
            db.session.commit()

        headers = [('Accept', 'application/json')]
        # test get without being authenticated
        with app.test_client() as client:
            res = client.get(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             headers=headers)
            assert res.status_code == 401
        # test not allowed get
        with app.test_client() as client:
            forbidden_login(client)
            res = client.get(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             headers=headers)
            assert res.status_code == 403
        # test allowed get
        with app.test_client() as client:
            allowed_login(client)
            res = client.get(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            pid, internal_record = resolver.resolve(response_data['id'])
            assert internal_record == response_data['metadata']


def test_patch_one_permissions(app, user_factory, resolver):
    """Test patch permission."""
    with app.app_context():
        # create the record using the internal API
        pid, internal_record = create_record(test_data)
        with user_factory('allowed') as allowed_user, \
                user_factory('forbidden') as forbidden_user:
            # create one user allowed to update the record
            allowed_user.update_access(True, str(internal_record.id))
            allowed_login = allowed_user.login_function()
            # create one user who is not allowed to update the record
            forbidden_user.update_access(False, str(internal_record.id))
            forbidden_login = forbidden_user.login_function()
            db.session.commit()

        headers = [('Content-Type', 'application/json-patch+json'),
                   ('Accept', 'application/json')]
        # test get without being authenticated
        with app.test_client() as client:
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 401
        # test not allowed get
        with app.test_client() as client:
            forbidden_login(client)
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 403
        # test allowed get
        with app.test_client() as client:
            allowed_login(client)
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            test = copy.deepcopy(test_data_patched)
            test['control_number'] = '1'
            assert response_data['metadata'] == test


def test_put_one_permissions(app, user_factory, resolver):
    """Test put permission."""
    with app.app_context():
        # create the record using the internal API
        pid, internal_record = create_record(test_data)
        with user_factory('allowed') as allowed_user, \
                user_factory('forbidden') as forbidden_user:
            # create one user allowed to update the record
            allowed_user.update_access(True, str(internal_record.id))
            allowed_login = allowed_user.login_function()
            # create one user who is not allowed to update the record
            forbidden_user.update_access(False, str(internal_record.id))
            forbidden_login = forbidden_user.login_function()
            db.session.commit()

        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'application/json')]
        # test get without being authenticated
        with app.test_client() as client:
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 401
        # test not allowed get
        with app.test_client() as client:
            forbidden_login(client)
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 403
        # test allowed get
        with app.test_client() as client:
            allowed_login(client)
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['metadata'] == test_data_patched


def test_delete_one_permissions(app, user_factory, resolver):
    """Test delete permission."""
    with app.app_context():
        # create the record using the internal API
        pid, internal_record = create_record(test_data)
        with user_factory('allowed') as allowed_user, \
                user_factory('forbidden') as forbidden_user:
            # create one user allowed to delete the record
            allowed_user.delete_access(True, str(internal_record.id))
            allowed_login = allowed_user.login_function()
            # create one user who is not allowed to delete the record
            forbidden_user.delete_access(False, str(internal_record.id))
            forbidden_login = forbidden_user.login_function()
            db.session.commit()

        headers = [('Content-Type', 'application/json')]
        # test get without being authenticated
        with app.test_client() as client:
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 401
        # test not allowed get
        with app.test_client() as client:
            forbidden_login(client)
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 403
        # test allowed get
        with app.test_client() as client:
            allowed_login(client)
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 204


def test_default_permissions(default_permissions):
    """Test default permissions."""
    app = default_permissions
    with app.app_context():
        pid, internal_record = create_record(test_data)
        headers = [('Content-Type', 'application/json')]
        fixtures = {'delete': 401, 'get': 200, 'post': 405, 'put': 401}
        with app.test_client() as client:
            for action, code in fixtures.items():
                request = getattr(client, action)
                res = request(url_for('invenio_records_rest.recid_item',
                                      pid_value=pid.pid_value),
                              headers=headers)
                assert code == res.status_code, action
