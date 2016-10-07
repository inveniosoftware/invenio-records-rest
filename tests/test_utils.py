# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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


"""Utils tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_records_rest.proxies import current_records_rest
from invenio_records_rest.utils import build_default_endpoint_prefixes


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            pid_type='recid',
            default_endpoint_prefix=False,
        )
    ),
)], indirect=['app'])
def test_build_default_endpoint_prefixes_simple(app):
    with app.test_client():
        assert current_records_rest.default_endpoint_prefixes['recid'] == \
            'recid'


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            pid_type='recid',
            default_endpoint_prefix=True,
        )
    ),
)], indirect=['app'])
def test_build_default_endpoint_prefixes_simple_with_default(app):
    with app.test_client():
        assert current_records_rest.default_endpoint_prefixes['recid'] == \
            'recid'


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            pid_type='recid',
            default_endpoint_prefix=False,
        ),
        recid2=dict(
            pid_type='recid',
            default_endpoint_prefix=False,
        )
    ),
)], indirect=['app'])
def test_build_default_endpoint_prefixes_two_simple_endpoints(app):
    with app.test_client():
        assert current_records_rest.default_endpoint_prefixes['recid'] == \
            'recid'


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            pid_type='recid',
            default_endpoint_prefix=True,
        ),
        recid2=dict(
            pid_type='recid',
            default_endpoint_prefix=False,
        )
    ),
)], indirect=['app'])
def test_build_default_endpoint_prefixes_redundant_default(app):
    with app.test_client():
        assert current_records_rest.default_endpoint_prefixes['recid'] == \
            'recid'


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            pid_type='recid',
            default_endpoint_prefix=False,
        ),
        recid2=dict(
            pid_type='recid',
            default_endpoint_prefix=True,
        )
    ),
)], indirect=['app'])
def test_build_default_endpoint_prefixes_two_endpoints_with_default(app):
    with app.test_client():
        assert current_records_rest.default_endpoint_prefixes['recid'] == \
            'recid2'


def test_get_default_endpoint_for_inconsistent(app):
    with pytest.raises(ValueError) as excinfo:
        build_default_endpoint_prefixes({
            'recid1': {
                'pid_type': 'recid',
                'default_endpoint_prefix': True,
            },
            'recid2': {
                'pid_type': 'recid',
                'default_endpoint_prefix': True,
            },
        })
    assert 'More than one' in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        build_default_endpoint_prefixes({
            'recid1': {
                'pid_type': 'recid',
            },
            'recid2': {
                'pid_type': 'recid',
            },
        })
    assert 'No endpoint-prefix' in str(excinfo.value)
