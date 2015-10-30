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


"""Module tests."""

from __future__ import absolute_import, print_function

import json

from flask import Flask, url_for
from invenio_records import Record
from jsonpatch import apply_patch
from six import string_types

from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.restful import RecordResource, RecordsListResource, \
    blueprint


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


def test_valid_create(app):
    """Test VALID record creation request (POST .../records/)."""
    with app.app_context():
        InvenioRecordsREST(app)
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.post(url_for(blueprint.name + '.' +
                                      RecordsListResource.view_name),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 201
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['data'] == test_data

            # check that an internal record returned id and that it contains
            # the same data
            assert 'id' in response_data.keys()
            internal_record = Record.get_record(response_data['id'])
            assert internal_record == response_data['data']

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_invalid_create(app):
    """Test INVALID record creation request (POST .../records/)."""
    with app.app_context():
        InvenioRecordsREST(app)
        with app.test_client() as client:
            # check that creating with non accepted format will return 406
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'video/mp4')]
            res = client.post(url_for(blueprint.name + '.' +
                                      RecordsListResource.view_name),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 406

            # check that creating with non-json Content-Type will return 400
            headers = [('Content-Type', 'video/mp4'),
                       ('Accept', 'application/json')]
            res = client.post(url_for(blueprint.name + '.' +
                                      RecordsListResource.view_name),
                              data=json.dumps(test_data),
                              headers=headers)
            assert res.status_code == 415

            # check that creating with invalid json will return 400
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.post(url_for(blueprint.name + '.' +
                                      RecordsListResource.view_name),
                              data='{fdssfd',
                              headers=headers)
            assert res.status_code == 400


def test_valid_get(app):
    """Test VALID record get request (GET .../records/<record_id>)."""
    with app.app_context():
        InvenioRecordsREST(app)
        # create the record using the internal API
        internal_record = Record.create(test_data)
        with app.test_client() as client:
            headers = [('Accept', 'application/json')]
            res = client.get(url_for(blueprint.name + '.' +
                                     RecordResource.view_name,
                                     record_id=internal_record.model.id),
                             headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['data'] == test_data

            # check the returned id
            assert 'id' in response_data.keys()
            assert response_data['id'] == internal_record.model.id

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_invalid_get(app):
    """Test INVALID record get request (GET .../records/<record_id>)."""
    with app.app_context():
        InvenioRecordsREST(app)
        with app.test_client() as client:
            # check that GET with non existing id will return 404
            headers = [('Accept', 'application/json')]
            res = client.get(url_for(blueprint.name + '.' +
                                     RecordResource.view_name, record_id=0),
                             headers=headers)
            assert res.status_code == 404

            # create the record using the internal API
            internal_record = Record.create(test_data)
            # check that GET with non accepted format will return 406
            headers = [('Accept', 'video/mp4')]
            res = client.get(url_for(blueprint.name + '.' +
                                     RecordResource.view_name,
                                     record_id=internal_record.model.id),
                             headers=headers)
            assert res.status_code == 406


def test_valid_patch(app):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    with app.app_context():
        InvenioRecordsREST(app)
        # create the record using the internal API
        internal_record = Record.create(test_data)
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for(blueprint.name + '.' +
                                       RecordResource.view_name,
                                       record_id=internal_record.model.id),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['data'] == test_data_patched

            # check that an internal record returned id and that it contains
            # the same data
            assert 'id' in response_data.keys()
            internal_record = Record.get_record(response_data['id'])
            assert internal_record == response_data['data']

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_invalid_patch(app):
    """Test INVALID record patch request (PATCH .../records/<record_id>)."""
    with app.app_context():
        InvenioRecordsREST(app)
        with app.test_client() as client:
            # check that PATCH with non existing id will return 404
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for(blueprint.name + '.' +
                                       RecordResource.view_name, record_id=0),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 404

            # create the record using the internal API
            internal_record = Record.create(test_data)
            # check that PATCH with non accepted format will return 406
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'video/mp4')]
            res = client.patch(url_for(blueprint.name + '.' +
                                       RecordResource.view_name,
                                       record_id=internal_record.model.id),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 406

            # check that PATCH with non-json Content-Type will return 400
            headers = [('Content-Type', 'video/mp4'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for(blueprint.name + '.' +
                                       RecordResource.view_name,
                                       record_id=internal_record.model.id),
                               data=json.dumps(test_patch),
                               headers=headers)
            assert res.status_code == 415

            # check that PATCH with invalid json-patch will return 400
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for(blueprint.name + '.' +
                                       RecordResource.view_name,
                                       record_id=internal_record.model.id),
                               data=json.dumps([
                                   {'invalid': 'json-patch'}
                               ]),
                               headers=headers)
            assert res.status_code == 400

            # check that PATCH with invalid json will return 400
            headers = [('Content-Type', 'application/json-patch+json'),
                       ('Accept', 'application/json')]
            res = client.patch(url_for(blueprint.name + '.' +
                                       RecordResource.view_name,
                                       record_id=internal_record.model.id),
                               data='{sdfsdf',
                               headers=headers)
            assert res.status_code == 400


def test_valid_put(app):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    with app.app_context():
        InvenioRecordsREST(app)
        # create the record using the internal API
        internal_record = Record.create(test_data)
        with app.test_client() as client:
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.put(url_for(blueprint.name + '.' +
                                     RecordResource.view_name,
                                     record_id=internal_record.model.id),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 200
            # check that the returned record matches the given data
            response_data = json.loads(res.get_data(as_text=True))
            assert response_data['data'] == test_data_patched

            # check that an internal record returned id and that it contains
            # the same data
            assert 'id' in response_data.keys()
            internal_record = Record.get_record(response_data['id'])
            assert internal_record == response_data['data']

            # check that the returned self link returns the same data
            subtest_self_link(response_data, res.headers, client)


def test_invalid_put(app):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    with app.app_context():
        InvenioRecordsREST(app)
        with app.test_client() as client:
            # check that PUT with non existing id will return 404
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.put(url_for(blueprint.name + '.' +
                                     RecordResource.view_name, record_id=0),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 404

            # create the record using the internal API
            internal_record = Record.create(test_data)
            # check that PUT with non accepted format will return 406
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'video/mp4')]
            res = client.put(url_for(blueprint.name + '.' +
                                     RecordResource.view_name,
                                     record_id=internal_record.model.id),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 406

            # check that PUT with non-json Content-Type will return 400
            headers = [('Content-Type', 'video/mp4'),
                       ('Accept', 'application/json')]
            res = client.put(url_for(blueprint.name + '.' +
                                     RecordResource.view_name,
                                     record_id=internal_record.model.id),
                             data=json.dumps(test_data_patched),
                             headers=headers)
            assert res.status_code == 415

            # check that PUT with invalid json will return 400
            headers = [('Content-Type', 'application/json'),
                       ('Accept', 'application/json')]
            res = client.put(url_for(blueprint.name + '.' +
                                     RecordResource.view_name,
                                     record_id=internal_record.model.id),
                             data='{invalid-json',
                             headers=headers)
            assert res.status_code == 400


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
    self_data = json.loads(self_response.get_data(as_text=True))
    assert self_data == response_data
    assert response_headers['Location'] == response_data['links']['self']
    assert response_headers['ETag'] == self_response.headers['ETag']
