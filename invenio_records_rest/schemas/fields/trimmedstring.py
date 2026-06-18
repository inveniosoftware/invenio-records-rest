# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Trimmed string field."""

from marshmallow import fields


class TrimmedString(fields.String):
    """String field which strips whitespace the ends of the string."""

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize string value."""
        value = super()._deserialize(value, attr, data, **kwargs)
        return value.strip()
