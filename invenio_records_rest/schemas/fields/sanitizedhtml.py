# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""HTML sanitized string field."""

import bleach
from flask import current_app

from .sanitizedunicode import SanitizedUnicode


class SanitizedHTML(SanitizedUnicode):
    """String field which strips sanitizes HTML using the bleach library."""

    def __init__(self, tags=None, attrs=None, *args, **kwargs):
        """Initialize field."""
        super().__init__(*args, **kwargs)
        self.tags = tags

        self.attrs = attrs

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize string by sanitizing HTML."""
        value = super()._deserialize(value, attr, data, **kwargs)
        return bleach.clean(
            value,
            tags=self.tags or current_app.config.get("ALLOWED_HTML_TAGS", []),
            attributes=self.attrs or current_app.config.get("ALLOWED_HTML_ATTRS", {}),
            strip=True,
        ).strip()
