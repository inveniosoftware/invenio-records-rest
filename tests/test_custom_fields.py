# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio custom schema fields tests."""

from invenio_records import Record

from invenio_records_rest.schemas import StrictKeysMixin
from invenio_records_rest.schemas.fields import DateString, SanitizedHTML, \
    SanitizedUnicode, TrimmedString


class CustomFieldSchema(StrictKeysMixin):
    """Test schema."""

    date_string_field = DateString(attribute='date_string_field')
    sanitized_html_field = SanitizedHTML(attribute='sanitized_html_field')
    sanitized_unicode_field = SanitizedUnicode(
        attribute='sanitized_unicode_field')
    trimmed_string_field = TrimmedString(
        attribute='trimmed_string_field')


def test_load_custom_fields(app):
    """Test pretty JSON."""
    rec = Record({'date_string_field': '27.10.1999',
                  'sanitized_html_field': 'an <script>evil()</script> example',
                  # Zero-width space, Line Tabulation, Escape, Cancel
                  'sanitized_unicode_field': u'\u200b\u000b\u001b\u0018',
                  'trimmed_string_field': 'so much trailing whitespace    '})

    with app.test_request_context():
        # ensure only valid keys are given
        CustomFieldSchema().check_unknown_fields(rec, rec)
        loaded_data = CustomFieldSchema().load(rec).data
        if 'metadata' in loaded_data:
            values = loaded_data['metadata'].values()
        else:
            values = loaded_data.values()
        assert set(values) == \
            set(['1999-10-27', 'so much trailing whitespace',
                 'an evil() example', u''])
