# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT


"""Extension initialization tests."""

from flask import Flask

from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter


def test_version():
    """Test version import."""
    from invenio_records_rest import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    app.url_map.converters["pid"] = PIDConverter
    ext = InvenioRecordsREST()
    assert "invenio-records-rest" not in app.extensions
    ext.init_app(app)
    assert "invenio-records-rest" in app.extensions
