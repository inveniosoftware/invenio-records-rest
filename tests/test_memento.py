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


"""PID resolver tests."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta
from time import sleep

import pytest
from flask import json, url_for
from helpers import create_record
from werkzeug.http import http_date, parse_date

RECORD_CLASS = 'invenio_records_rest.memento:MementoRecord'


@pytest.mark.parametrize('app', [dict(endpoint=dict(
    record_class=RECORD_CLASS,
    item_route='/records/<pid(recid, record_class="{0}"):pid_value>'.format(
        RECORD_CLASS
    ),
))], indirect=['app'])
def test_record_mementos(app, db):
    """Test resolution of record mementos."""
    modifications = [(datetime.now() + timedelta(days=-1), 'test')]
    pid, record = create_record({'title': 'test'})
    db.session.commit()
    assert len(record.revisions) == 1
    modifications.append((record.model.updated, 'test'))

    sleep(1)
    record.update({'title': 'test1'})
    record.commit()
    db.session.commit()
    assert len(record.revisions) == 2

    modifications.append((record.model.updated, 'test1'))
    modifications.append((datetime.now() + timedelta(days=1), 'test1'))

    headers = [('Accept', 'application/json')]
    with app.test_client() as client:
        # Normal request
        res = client.get(
            url_for('invenio_records_rest.recid_item',
                    pid_value=pid.pid_value),
            headers=headers)
        assert res.status_code == 200
        assert 'Memento-Datetime' not in res.headers

        for i, (accept_datetime, title) in enumerate(modifications):
            res = client.get(
                url_for('invenio_records_rest.recid_item',
                        pid_value=pid.pid_value),
                headers=headers + [
                    ('Accept-Datetime', http_date(accept_datetime))
                ],
            )
            assert res.status_code == 200, i
            assert parse_date(res.headers['Memento-Datetime']), i
            assert title == json.loads(
                res.data
            )['metadata']['title'], i
