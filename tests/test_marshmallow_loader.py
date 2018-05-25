# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio marshmallow loader tests."""

from __future__ import absolute_import, print_function

import json

import pytest
from helpers import get_json
from marshmallow import Schema, fields

import invenio_records_rest.serializers.loaders as loaders
from invenio_records_rest.serializers.schemas.json import RecordSchemaJSONV1


class TestSchema(Schema):
        """Test schema."""

        title = fields.Str(required=True, attribute='metadata.mytitle')
        random = fields.Str(required=True, attribute='metadata.nonexistant')
        id = fields.Str(attribute='pid.pid_value')


def test_marshmallow_load(app, db, es, test_data, search_url, search_class):
    """Test marshmallow loader."""
    app.config['RECORDS_REST_DEFAULT_LOADERS'] = {
        'application/json': loaders.json_v1,
        'application/json-patch+json': loaders.json_patch_v1,
    }

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 201

        # Check that the returned record matches the given data
        data = get_json(res)
        assert RecordSchemaJSONV1().load(data)


def test_marshmallow_load_errors(app, db, es, test_data, search_url,
                                 search_class):
    """Test marshmallow loader."""

    app.config['RECORDS_REST_DEFAULT_LOADERS'] = {
        'application/json': loaders.marshmallow.marshmallow_loader(TestSchema),
        'application/json-patch+json': loaders.json_patch_v1,
    }

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]

        # Create record
        incomplete_data = dict(test_data[0])
        del incomplete_data['title']
        res = client.post(
            search_url, data=json.dumps(incomplete_data), headers=HEADERS)
        assert res.status_code == 400


def test_marshmallow_errors(test_data):
    """Test MarshmallowErrors class."""
    incomplete_data = dict(test_data[0])
    res = TestSchema(context={}).load(json.dumps(incomplete_data))
    me = loaders.marshmallow.MarshmallowErrors(res.errors)

    with pytest.raises(TypeError):
        next(me)
    # assert __iter__ method works
    iter(me)
    # assert __next__ method works
    assert next(me)
