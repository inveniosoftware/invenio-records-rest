# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Delete record tests."""

from __future__ import absolute_import, print_function

from flask import url_for
from helpers import get_json, record_url
from invenio_pidstore.models import PersistentIdentifier
from mock import patch
from sqlalchemy.exc import SQLAlchemyError


def test_valid_delete(app, test_records):
    """Test VALID record delete request (DELETE .../records/<record_id>)."""
    # Test with and without headers
    for i, headers in enumerate([[], [('Accept', 'video/mp4')]]):
        pid, record = test_records[i]
        with app.test_client() as client:
            res = client.delete(record_url(pid), headers=headers)
            assert res.status_code == 204

            res = client.get(record_url(pid))
            assert res.status_code == 410


def test_delete_deleted(app, test_records):
    """Test deleting a perviously deleted record."""
    pid, record = test_records[0]

    with app.test_client() as client:
        res = client.delete(record_url(pid))
        assert res.status_code == 204

        res = client.delete(record_url(pid))
        assert res.status_code == 410
        data = get_json(res)
        assert 'message' in data
        assert data['status'] == 410


def test_delete_notfound(app, test_records):
    """Test INVALID record delete request (DELETE .../records/<record_id>)."""
    with app.test_client() as client:
        # Check that GET with non existing id will return 404
        res = client.delete(url_for(
            'invenio_records_rest.recid_item', pid_value=0))
        assert res.status_code == 404


def test_delete_with_sqldatabase_error(app, test_records):
    """Test VALID record delete request (GET .../records/<record_id>)."""
    pid, record = test_records[0]

    with app.test_client() as client:
        def raise_error():
            raise SQLAlchemyError()
        # Force an SQLAlchemy error that will rollback the transaction.
        with patch.object(PersistentIdentifier, 'delete',
                          side_effect=raise_error):
            res = client.delete(record_url(pid))
            assert res.status_code == 500

    with app.test_client() as client:
            res = client.get(record_url(pid))
            assert res.status_code == 200
