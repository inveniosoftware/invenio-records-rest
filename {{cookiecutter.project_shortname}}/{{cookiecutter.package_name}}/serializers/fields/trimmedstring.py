{% include 'misc/header.py' %}
"""Trimmed string field."""

from __future__ import absolute_import, print_function

from marshmallow import fields


class TrimmedString(fields.String):
    """String field which strips whitespace the ends of the string."""

    def _deserialize(self, value, attr, data):
        """Deserialize string value."""
        value = super(TrimmedString, self)._deserialize(value, attr, data)
        return value.strip()
