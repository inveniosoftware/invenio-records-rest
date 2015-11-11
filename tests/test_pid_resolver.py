# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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


"""Module tests."""

from __future__ import absolute_import, print_function

import copy
import uuid

from flask import url_for
from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import Record


def create_record(data):
    """Create a test record."""
    with db.session.begin_nested():
        data = copy.deepcopy(data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid_minter'](rec_uuid, data)
        record = Record.create(data, id_=rec_uuid)
    return pid, record


def control_num(data, cn=1):
    """Inject a control number in data."""
    data = copy.deepcopy(data)
    data['control_number'] = cn
    return data


def test_tombstone(app):
    """Test tomstones."""
    with app.app_context():
        # OK PID
        pid_ok, record = create_record({'title': 'test'})

        # Deleted PID
        pid_del, record = create_record({'title': 'deleted'})
        pid_del.delete()

        # Missing object PID
        pid_noobj = PersistentIdentifier.create(
            'recid', '100', status=PIDStatus.REGISTERED)
        db.session.commit()

        # Redirected PID
        pid_red = PersistentIdentifier.create(
            'recid', '101', status=PIDStatus.REGISTERED)
        pid_red.redirect(pid_ok)

        # Redirect PID - different endpoint
        pid_doi = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.REGISTERED)
        pid_red_doi = PersistentIdentifier.create(
            'recid', '102', status=PIDStatus.REGISTERED)
        pid_red_doi.redirect(pid_doi)
        db.session.commit()

        with app.test_client() as client:
            # PID deleted
            headers = [('Accept', 'application/json')]
            res = client.get(
                url_for('invenio_records_rest.recid_item',
                        pid_value=pid_del.pid_value),
                headers=headers)
            assert res.status_code == 410

            # PID missing object
            res = client.get(
                url_for('invenio_records_rest.recid_item',
                        pid_value=pid_noobj.pid_value),
                headers=headers)
            assert res.status_code == 500

            # Redirected invalid endpoint
            res = client.get(
                url_for('invenio_records_rest.recid_item',
                        pid_value=pid_red_doi.pid_value),
                headers=headers)
            assert res.status_code == 500

            # Redirected
            res = client.get(
                url_for('invenio_records_rest.recid_item',
                        pid_value=pid_red.pid_value),
                headers=headers)
            assert res.status_code == 301
