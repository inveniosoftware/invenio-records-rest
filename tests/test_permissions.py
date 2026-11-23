# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT


"""Permissions tests."""

import json

import pytest
from flask_login import LoginManager, UserMixin
from helpers import record_url

from invenio_records_rest import config


@pytest.fixture(scope="module")
def base_app(base_app):
    """Allow easy login for tests purposes: ``?user=<id>``.

    Set up before the first request is handled, as Flask does not allow
    it later on.
    """
    lm = LoginManager(base_app)

    class User(UserMixin):
        def __init__(self, id):
            self.id = id

    @lm.request_loader
    def load_user(request):
        uid = request.args.get("user", type=int)
        if uid:
            return User(uid)
        return None

    yield base_app


@pytest.fixture()
def default_permissions(app, set_app_config_fn_scoped):
    """Test default deny all permission."""
    set_app_config_fn_scoped(
        {
            key: getattr(config, key)
            for key in [
                "RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY",
                "RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY",
                "RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY",
                "RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY",
            ]
        }
    )
    # The factories are cached on the extension, so drop them before and after.
    app.extensions["invenio-records-rest"].reset_permission_factories()
    yield app
    app.extensions["invenio-records-rest"].reset_permission_factories()


def test_default_permissions(
    app, default_permissions, test_data, search_url, test_records, indexed_records
):
    """Test default create permissions."""
    pid, record = test_records[0]
    rec_url = record_url(pid)
    data = json.dumps(test_data[0])
    h = {"Content-Type": "application/json"}
    hp = {"Content-Type": "application/json-patch+json"}

    with app.test_client() as client:
        args = dict(data=data, headers=h)
        pargs = dict(data=data, headers=hp)
        qs = {"user": "1"}
        uargs = dict(data=data, headers=h, query_string=qs)
        upargs = dict(data=data, headers=hp, query_string=qs)

        assert client.get(search_url).status_code == 200
        assert client.get(rec_url).status_code == 200

        assert 401 == client.post(search_url, **args).status_code
        assert 405 == client.put(search_url, **args).status_code
        assert 405 == client.patch(search_url).status_code
        assert 405 == client.delete(search_url).status_code

        assert 405 == client.post(rec_url, **args).status_code
        assert 401 == client.put(rec_url, **args).status_code
        assert 401 == client.patch(rec_url, **pargs).status_code
        assert 401 == client.delete(rec_url).status_code

        assert 403 == client.post(search_url, **uargs).status_code
        assert 403 == client.put(rec_url, **uargs).status_code
        assert 403 == client.patch(rec_url, **upargs).status_code
        assert 403 == client.delete(rec_url, query_string=qs).status_code
