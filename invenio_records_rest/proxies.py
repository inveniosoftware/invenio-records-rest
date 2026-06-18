# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""REST API for Records."""

from flask import current_app
from werkzeug.local import LocalProxy

current_records_rest = LocalProxy(
    lambda: current_app.extensions["invenio-records-rest"]
)
"""Proxy to an instance of ``_RecordRESTState``."""
