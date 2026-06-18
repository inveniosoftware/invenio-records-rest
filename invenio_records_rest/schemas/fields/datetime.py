# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Date string field."""

import arrow
from arrow.parser import ParserError
from marshmallow import fields, missing


class DateString(fields.Date):
    """ISO8601-formatted date string."""

    def _serialize(self, value, attr, obj, **kwargs):
        """Serialize an ISO8601-formatted date."""
        try:
            return super()._serialize(arrow.get(value).date(), attr, obj, **kwargs)
        except ParserError:
            return missing

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize an ISO8601-formatted date."""
        return super()._deserialize(value, attr, data, **kwargs).isoformat()
