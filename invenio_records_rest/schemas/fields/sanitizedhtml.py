# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""HTML sanitized string field."""

from __future__ import absolute_import, print_function

import bleach
from flask import current_app

from .sanitizedunicode import SanitizedUnicode


class SanitizedHTML(SanitizedUnicode):
    """String field which strips sanitizes HTML using the bleach library."""

    def __init__(self, tags=None, attrs=None, *args, **kwargs):
        """Initialize field."""
        super(SanitizedHTML, self).__init__(*args, **kwargs)
        self.tags = tags

        self.attrs = attrs

    def _deserialize(self, value, attr, data):
        """Deserialize string by sanitizing HTML."""
        value = super(SanitizedHTML, self)._deserialize(value, attr, data)
        return bleach.clean(
            value,
            tags=self.tags or current_app.config.get('ALLOWED_HTML_TAGS', []),
            attributes=self.attrs or current_app.config.get(
                'ALLOWED_HTML_ATTRS', {}),
            strip=True,
        ).strip()
