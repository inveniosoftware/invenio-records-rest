# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C) 2017-2018 Swiss Data Science Center (SDSC)
# A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
# Eidgenössische Technische Hochschule Zürich (ETHZ).
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Utils tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_records_rest.proxies import current_records_rest
from invenio_records_rest.utils import LazyPIDValue, \
    build_default_endpoint_prefixes


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


def test_lazy_pid_value():
    """Test lazy PID value."""
    pid = LazyPIDValue(None, 1)

    assert str(pid) == '1'

    repr_pid = eval(repr(pid))
    assert repr_pid.value == pid.value
    assert repr_pid.resolver == pid.resolver
