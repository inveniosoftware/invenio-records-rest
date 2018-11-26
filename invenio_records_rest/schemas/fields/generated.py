# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Generated field."""

from __future__ import absolute_import, print_function

from marshmallow import fields

from invenio_records_rest.utils import obj_or_import_string


class Generated(fields.Field):
    """Custom Generate class to inject PID from context."""

    def __init__(self, ser_callback=None, de_callback=None, *args, **kwargs):
        """Enforce deserialization."""
        if de_callback:
            kwargs['missing'] = None  # enforce calling `deseralize`
            deserializer = obj_or_import_string(de_callback)
            self._de_callback = deserializer
        if ser_callback:
            kwargs['default'] = None
            serializer = obj_or_import_string(ser_callback)
            self._ser_callback = serializer

        super(Generated, self).__init__(*args, **kwargs)

    def serialize(self, attr, obj, accessor=None):
        """Serialize by returning the value of missing."""
        """Get PID value from context."""
        if self._ser_callback:
            if isinstance(self._ser_callback, str):
                func = getattr(self.parent, self._ser_callback)
                return func()

            return self._ser_callback(self.parent, attr, obj, accessor)
        else:
            super(Generated, self)._serialize(attr, obj, accessor)

    def deserialize(self, value, attr=None, data=None):
        """Get PID value from context."""
        if self._de_callback:
            if isinstance(self._de_callback, str):
                func = getattr(self.parent, self._de_callback)
                return func()

            return self._de_callback(self.parent, value, attr, data)
        else:
            super(Generated, self)._deserialize(value, attr, data)
