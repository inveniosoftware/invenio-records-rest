# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent Identifier field."""

from marshmallow import fields, missing


class PersistentIdentifier(fields.Field):
    """Field to handle PersistentIdentifiers in records.

    .. versionadded:: 1.2.0
    """

    def _serialize(self, value, attr, context):
        pid = context.get('pid')
        return pid.pid_value if pid else missing

    def _deserialize(self, value, attr, context):
        pid = context.get('pid')
        return pid.get('pid_value') if pid else missing
