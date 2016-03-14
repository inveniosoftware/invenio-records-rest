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

"""Helper methods for tests."""

import copy
import json
import uuid

from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_records import Record
from jsonpatch import apply_patch
from six import string_types

test_data = {
    'title': 'Back to the Future',
    'year': 2015,
    'stars': 4,
}

test_data2 = {
    'title': 'Back to the Past',
    'year': 2042,
    'stars': 3,
}

test_data3 = {
    'title': 'The Hitchhiker\'s Guide to the Galaxy',
    'year': 1985,
    'stars': 4,
}

test_data4 = {
    'title': 'Unknown film',
    'year': 4242,
    'stars': 5,
}

test_patch = [
    {'op': 'replace', 'path': '/year', 'value': 1985},
]

test_data_patched = apply_patch(test_data, test_patch)


def create_record(data):
    """Create a test record."""
    with db.session.begin_nested():
        data = copy.deepcopy(data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid'](rec_uuid, data)
        record = Record.create(data, id_=rec_uuid)
    return pid, record


def control_num(data, cn=1):
    """Inject a control number in data."""
    data = copy.deepcopy(data)
    data['control_number'] = str(cn)
    return data


def subtest_self_link(response_data, response_headers, client):
    """Check that the returned self link returns the same data.

    Also, check that headers have the same link as 'Location'.
    """
    assert 'links' in response_data.keys() \
        and isinstance(response_data['links'], dict)
    assert 'self' in response_data['links'].keys() \
        and isinstance(response_data['links']['self'], string_types)
    headers = [('Accept', 'application/json')]
    self_response = client.get(response_data['links']['self'],
                               headers=headers)

    assert self_response.status_code == 200
    self_data = json.loads(self_response.get_data(as_text=True))
    assert self_data == response_data
    if response_headers:
        assert response_headers['ETag'] == self_response.headers['ETag']
