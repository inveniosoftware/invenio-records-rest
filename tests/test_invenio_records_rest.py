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


"""Module tests."""

from __future__ import absolute_import, print_function

import copy
import json
import uuid

import pytest
from flask import Flask, url_for
from invenio_db import db
from invenio_records import Record
from jsonpatch import apply_patch
from mock import patch
from six import string_types
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest import InvenioRecordsREST


def test_version():
    """Test version import."""
    from invenio_records_rest import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    app.config.update(SERVER_NAME='http://localhost:5000/')
    ext = InvenioRecordsREST()
    assert 'invenio-records-rest' not in app.extensions
    ext.init_app(app)
    assert 'invenio-records-rest' in app.extensions


test_data = {
    'title': 'Back to the Future',
    'year': 2015,
}

test_patch = [
    {'op': 'replace', 'path': '/year', 'value': 1985},
]

test_data_patched = apply_patch(test_data, test_patch)


def create_record(data):
    """Create a test record."""
    with db.session.begin_nested():
        data = copy.deepcopy(data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid_minter'](rec_uuid, data)
        record = Record.create(data, id_=rec_uuid)
    return pid, record


def delete_record(pid, app):
    """Delete a given record."""
    with app.test_client() as client:
        headers = [('Accept', 'application/json')]
        res = client.delete(url_for('invenio_records_rest.recid_item',
                                    pid_value=pid.pid_value),
                            headers=headers)
        assert res.status_code == 204


def control_num(data, cn=1):
    """Inject a control number in data."""
    data = copy.deepcopy(data)
    data['control_number'] = cn
    return data


def test_valid_delete(app):
    """Test VALID record delete request (DELETE .../records/<record_id>)."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)

        with app.test_client() as client:
            headers = [('Accept', 'application/json')]
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 204
            # check database state
            with pytest.raises(NoResultFound):
                Record.get_record(record.id)
            assert pid.is_deleted()

            # check that DELETE with non JSON accepted format will work
            # as it returns nothing
            pid, record = create_record(test_data)
            headers = [('Accept', 'video/mp4')]
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 204


def test_delete_deleted(app):
    """Test deleting a perviously deleted record."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)
        delete_record(pid, app)

        with app.test_client() as client:
            headers = [('Accept', 'application/json')]
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 410
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['status'] == 410
            assert 'no longer available' in response_data['message']


def test_invalid_delete(app):
    """Test INVALID record delete request (DELETE .../records/<record_id>)."""
    with app.app_context():
        with app.test_client() as client:
            # check that GET with non existing id will return 404
            headers = [('Accept', 'application/json')]
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=0),
                                headers=headers)
            assert res.status_code == 404

            # check that deleting a deleted record returns 410
            pid, record = create_record(test_data)
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 204
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid.pid_value),
                                headers=headers)
            assert res.status_code == 410


def test_delete_with_sqldatabase_error(app):
    """Test VALID record delete request (GET .../records/<record_id>)."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)
        db.session.expire(record.model)
        pid_value = pid.pid_value
        pid_type = pid.pid_type
        record_id = record.id

        db.session.commit()
        Record.get_record(record_id)

        def raise_exception():
            raise SQLAlchemyError()

        with app.test_client() as client:
            # start a new SQLAlchemy session so that it will rollback
            # everything
            nested_transaction = db.session().transaction
            orig_rollback = nested_transaction.rollback
            flags = {'rollbacked': False}

            def custom_rollback(*args, **kwargs):
                flags['rollbacked'] = True
                orig_rollback(*args, **kwargs)
            nested_transaction.rollback = custom_rollback

            with patch.object(PersistentIdentifier, 'delete',
                              side_effect=raise_exception):
                headers = [('Accept', 'application/json')]
                res = client.delete(url_for('invenio_records_rest.recid_item',
                                            pid_value=pid_value),
                                    headers=headers)
                assert res.status_code == 500
            # check that the transaction is finished
            assert db.session().transaction is not nested_transaction
            # check that the session has rollbacked
            assert flags['rollbacked']

    with app.app_context():
        with app.test_client() as client:
            # check that the record and PID have not been deleted
            Record.get_record(record_id)
            assert not PersistentIdentifier.get(pid_type,
                                                pid_value).is_deleted()
            # try to delete without exception, the transaction should have been
            # rollbacked
            headers = [('Accept', 'application/json')]
            res = client.delete(url_for('invenio_records_rest.recid_item',
                                        pid_value=pid_value),
                                headers=headers)
            assert res.status_code == 204
            # check database state
            with pytest.raises(NoResultFound):
                Record.get_record(record_id)
            assert PersistentIdentifier.get(pid_type,
                                            pid_value).is_deleted()


def test_valid_create(app, resolver):
    """Test VALID record creation request (POST .../records/)."""
    with app.app_context():
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 201
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            # note that recid_minter ingests the control_number.
            assert response_data['metadata'] == control_num(test_data)

            # check that an internal record returned id and that it contains
            # the same data
            assert 'id' in response_data.keys()
            pid, internal_record = resolver.resolve(response_data['id'])
            assert internal_record == response_data['metadata']

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_invalid_create(app):
    """Test INVALID record creation request (POST .../records/)."""
    with app.app_context():
        with app.test_client() as client:
            # check that creating with non accepted format will return 406
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'video/mp4')]
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 406

            # Check that creating with non-json Content-Type will return 400
            headers = [('Content-Type', 'video/mp4'),
                       ('Accept', 'application/json')]
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 415

            # check that creating with invalid json will return 400
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              data='{fdssfd',
                              headers=headers)
            assert res.status_code == 400

            # check that creating with no content will return 400
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.post(url_for('invenio_records_rest.recid_list'),
                              headers=headers)
            assert res.status_code == 400

            # Bad internal error:
            with patch('invenio_records_rest.views.db.session.commit') as mock:
                mock.side_effect = SQLAlchemyError()

                headers = [('Content-Type', 'application/json'),
                           ('Accept', 'application/json')]
                res = client.post(url_for('invenio_records_rest.recid_list'),
                                  data=json.dumps(test_data),
                                  headers=headers)
                assert res.status_code == 500


def test_valid_get(app):
    """Test VALID record get request (GET .../records/<record_id>)."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)

        with app.test_client() as client:
            headers = [('Accept', 'application/json')]
            res = client.get(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['metadata'] == control_num(test_data)

            # check the returned id
            assert 'id' in response_data.keys()
            assert response_data['id'] == pid.pid_value

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_get_deleted(app):
    """Test getting deleted record."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)
        delete_record(pid, app)

        with app.test_client() as client:
            headers = [('Accept', 'application/json')]
            # check get response for deleted resource
            get_res = client.get(url_for('invenio_records_rest.recid_item',
                                         pid_value=pid.pid_value),
                                 headers=headers)
            assert get_res.status_code == 410
            # check that the returned record matches the given data
            response_data = json.loads(get_res.get_data(as_text=True))
            assert response_data['status'] == 410
            assert 'no longer available' in response_data['message']


def test_invalid_get(app):
    """Test INVALID record get request (GET .../records/<record_id>)."""
    with app.app_context():
        with app.test_client() as client:
            # check that GET with non existing id will return 404
            headers = [('Accept', 'application/json')]
            res = client.get(url_for('invenio_records_rest.recid_item',
                                     pid_value='0'),
                             headers=headers)
            assert res.status_code == 404

            # create the record using the internal API
            pid, record = create_record(test_data)

            # check that GET with non accepted format will return 406
            headers = [('Accept', 'video/mp4')]
            res = client.get(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             headers=headers)
            assert res.status_code == 406


def test_valid_patch(app, resolver):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    with app.app_context():
        # create the record using the internal API
        pid, internal_record = create_record(test_data)
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            test = copy.deepcopy(test_data_patched)
            test['control_number'] = 1
            assert response_data['metadata'] == test

            # check that an internal record returned id and that it contains
            # the same data
            assert 'id' in response_data.keys()
            pid, internal_record = resolver.resolve(response_data['id'])
            assert internal_record == response_data['metadata']

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_patch_deleted(app):
    """Test patching deleted record."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)
        delete_record(pid, app)

        with app.test_client() as client:
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            # check patch response for deleted resource
            patch_res = client.patch(url_for('invenio_records_rest.recid_item',
                                             pid_value=pid.pid_value),
                                     data=json.dumps(test_patch),
                                     headers=headers)
            assert patch_res.status_code == 410
            # check that the returned record matches the given data
            response_data = json.loads(patch_res.get_data(as_text=True))
            assert response_data['status'] == 410
            assert 'no longer available' in response_data['message']


def test_invalid_patch(app):
    """Test INVALID record patch request (PATCH .../records/<record_id>)."""
    with app.app_context():
        with app.test_client() as client:
            # check that PATCH with non existing id will return 404
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=0),
                               headers=headers)
            assert res.status_code == 404

            # create the record using the internal API
            pid, internal_record = create_record(test_data)

            # check that PATCH with non accepted format will return 406
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'video/mp4')]
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 406

            # check that PATCH with non-json Content-Type will return 415
            headers = [('Content-Type', 'video/mp4'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 415

            # check that PATCH with invalid json-patch will return 400
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data=json.dumps([
                                   {'invalid': 'json-patch'}
                               ]),
                               headers=headers)
            assert res.status_code == 400

            # check that PATCH with invalid json will return 400
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for('invenio_records_rest.recid_item',
                                       pid_value=pid.pid_value),
                               data='{sdfsdf',
                               headers=headers)
            assert res.status_code == 400


def test_valid_put(app, resolver):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    with app.app_context():
        # create the record using the internal API
        pid, internal_record = create_record(test_data)
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['metadata'] == test_data_patched

            # check that an internal record returned id and that it contains
            # the same data
            assert 'id' in response_data.keys()
            pid, internal_record = resolver.resolve(response_data['id'])
            assert internal_record == response_data['metadata']

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_put_deleted(app):
    """Test putting deleted record."""
    with app.app_context():
        # create the record using the internal API
        pid, record = create_record(test_data)
        delete_record(pid, app)

        with app.test_client() as client:
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            # check put response for deleted resource
            put_res = client.put(url_for('invenio_records_rest.recid_item',
                                         pid_value=pid.pid_value),
                                 data=json.dumps(test_data_patched),
                                 headers=headers)
            assert put_res.status_code == 410
            # check that the returned record matches the given data
            response_data = json.loads(put_res.get_data(as_text=True))
            assert response_data['status'] == 410
            assert 'no longer available' in response_data['message']


def test_invalid_put(app):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    with app.app_context():
        with app.test_client() as client:
            # check that PUT with non existing id will return 404
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value='0'),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 404

            # create the record using the internal API
            pid, internal_record = create_record(test_data)

            # check that PUT with non accepted format will return 406
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'video/mp4')]
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 406

            # check that PUT with non-json Content-Type will return 415
            headers = [('Content-Type', 'video/mp4'),
                       ('Accept', 'application/json')]
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 415

            # check that PUT with invalid json will return 400
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.put(url_for('invenio_records_rest.recid_item',
                                     pid_value=pid.pid_value),
                             data='{invalid-json',
                             headers=headers)
            assert res.status_code == 400


def test_create_permissions(app, user_factory, resolver):
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
            test['control_number'] = 1
            assert response_data['metadata'] == test


def test_put_one_permissions(app, user_factory, resolver):
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


def subtest_self_link(response_data, response_headers, client):
    """Check that the returned self link returns the same data.

    Also, check that headers have the same link as 'Location'.
    """
    assert 'links' in response_data.keys() \
        and isinstance(response_data['links'], dict)
    assert 'self' in response_data['links'].keys() \
        and isinstance(response_data['links']['self'], string_types)
    headers = [('Accept', 'application/json')]
    self_response = client.get(response_data['links']['self'],
                               headers=headers)
    assert self_response.status_code == 200
    self_data = json.loads(self_response.get_data(as_text=True))
    assert self_data == response_data
    assert response_headers['Location'] == response_data['links']['self']
    assert response_headers['ETag'] == self_response.headers['ETag']
