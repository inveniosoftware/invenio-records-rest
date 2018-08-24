# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow JSON schema."""

from __future__ import absolute_import, print_function

from marshmallow import Schema, ValidationError, fields, missing, \
    validates_schema


class StrictKeysMixin(Schema):
    """Ensure only valid keys exists."""

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        """Check for unknown keys."""
        if isinstance(original_data, list):
            for elem in original_data:
                self.check_unknown_fields(data, elem)
        else:
            for key in original_data:
                if key not in [
                        self.fields[field].attribute or field
                        for field in self.fields
                ]:
                    raise ValidationError(
                        'Unknown field name {}'.format(key), field_names=[key])


class RecordSchemaJSONV1(Schema):
    """Schema for records v1 in JSON."""

    id = fields.Integer(attribute='pid.pid_value')
    metadata = fields.Raw()
    links = fields.Raw()
    created = fields.Str()
    updated = fields.Str()


class Nested(fields.Nested):
    """Custom Nested class to not recursively check errors.

    .. versionadded:: 1.2.0
    """

    def _validate_missing(self, value):
        if value is missing and getattr(self, 'required', False):
            self.fail('required')
        return super()._validate_missing(value)
