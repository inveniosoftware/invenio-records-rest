# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent Identifier field."""

from marshmallow import missing

from invenio_records_rest.schemas.fields import Generated


def default_pid_deserializer(schema, value, attr, accesor):
    """Custom PID deserializer function."""
    if schema.context and schema.context.get('pid'):
        pid = schema.context.get('pid')
        return pid.pid_value
    return missing


def default_pid_serializer(schema, value, attr, data):
    """Custom PID serializer function."""
    pid = schema.context.get('pid')
    return pid.pid_value


class PersistentIdentifier(Generated):
    """Field to handle PersistentIdentifiers in records.

    .. versionadded:: 1.2.0
    """

    def __init__(self, *args, **kwargs):
        """Initialize field."""
        super(PersistentIdentifier, self).__init__(default_pid_serializer,
                                                   default_pid_deserializer,
                                                   *args, **kwargs)
