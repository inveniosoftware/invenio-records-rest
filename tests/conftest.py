# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Pytest configuration."""

import copy
import json
import os
import sys
from os.path import dirname, join

import pytest
from flask import url_for
from helpers import create_record
from invenio_app.factory import create_api
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index
from invenio_search import RecordsSearch, current_search

from invenio_records_rest import config
from invenio_records_rest.facets import terms_filter

sys.path.append(os.path.dirname(__file__))


class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = "invenio-records-rest"

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{"_source": {"excludes": ["_access"]}})


class IndexFlusher(object):
    """Simple object to flush an index."""

    def __init__(self, search_class):
        """Initialize instance."""
        self.search_class = search_class

    def flush_and_wait(self):
        """Flush index and wait until operation is fully done."""
        current_search.flush_and_refresh(self.search_class.Meta.index)


@pytest.fixture(scope="session")
def search_class():
    """Search class."""
    yield TestSearch


@pytest.fixture()
def search_url():
    """Search class."""
    yield url_for("invenio_records_rest.recid_list")


@pytest.fixture(scope="module")
def extra_entry_points():
    """Register the test mappings."""
    return {
        "invenio_search.mappings": [
            "invenio-records-rest = mock_module.mappings",
        ],
    }


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config, request, search_class):
    """Application configuration fixture.

    Note that RECORDS_REST_ENDPOINTS is used during application creation to
    create blueprints on the fly, hence once you have the app in a test,
    it's too late to customize the configuration variable. You can however
    customize it using indirectly parameterized tests:

    .. code-block:: python

    @pytest.mark.parametrize('app_config', [dict(
        endpoint=dict(
            search_class='conftest:TestSearch',
        )
    )], indirect=['app_config'])
    def test_mytest(app, db, search):
        # ...

    This will parameterize the default 'recid' endpoint in
    RECORDS_REST_ENDPOINTS.

    Alternatively:

    .. code-block:: python

    @pytest.mark.parametrize('app_config', [dict(
        records_rest_endpoints=dict(
            recid=dict(
                search_class='conftest:TestSearch',
            )
        )
    )], indirect=['app_config'])
    def test_mytest(app, db, search):
        # ...

    This will fully parameterize RECORDS_REST_ENDPOINTS.

    Each distinct parameter gets its own (module-scoped) application.
    """
    # pytest-invenio's app_config is shared by all parameter variants within
    # a module, so work on a copy to keep the variants from leaking.
    app_config = dict(app_config)
    app_config.update(
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_DOC_TYPE="testrecord",
        INDEXER_DEFAULT_INDEX=search_class.Meta.index,
        REST_MIMETYPE_QUERY_ARG_NAME="format",
        RECORDS_REST_ENDPOINTS=copy.deepcopy(config.RECORDS_REST_ENDPOINTS),
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_RESULTS_SIZE=10,
        RECORDS_REST_DEFAULT_SEARCH_INDEX=search_class.Meta.index,
        RECORDS_REST_FACETS={
            search_class.Meta.index: {
                "aggs": {"stars": {"terms": {"field": "stars"}}},
                "post_filters": {
                    "stars": terms_filter("stars"),
                },
            }
        },
        RECORDS_REST_SORT_OPTIONS={
            search_class.Meta.index: dict(
                year=dict(
                    fields=["year"],
                )
            )
        },
        SERVER_NAME="localhost:5000",
    )
    endpoints = app_config["RECORDS_REST_ENDPOINTS"]
    endpoints["recid"]["search_class"] = search_class

    # Parameterize application.
    if hasattr(request, "param"):
        if "endpoint" in request.param:
            endpoints["recid"].update(request.param["endpoint"])
        if "records_rest_endpoints" in request.param:
            original_endpoint = endpoints.pop("recid")
            for new_endpoint_prefix, new_endpoint_value in request.param[
                "records_rest_endpoints"
            ].items():
                new_endpoint = dict(original_endpoint)
                new_endpoint.update(new_endpoint_value)
                endpoints[new_endpoint_prefix] = new_endpoint

    return app_config


def record_indexer_receiver(sender, json=None, record=None, index=None, **kwargs):
    """Mock-receiver of a before_record_index signal."""
    suggest_byyear = {}
    suggest_byyear["contexts"] = {"year": [str(json["year"])]}
    suggest_byyear["input"] = [
        json["title"],
    ]

    suggest_title = {}
    suggest_title["input"] = [
        json["title"],
    ]
    json["suggest_byyear"] = suggest_byyear
    json["suggest_title"] = suggest_title
    return json


@pytest.fixture()
def indexer(app, search_clear):
    """Create a record indexer."""
    before_record_index.connect(record_indexer_receiver, sender=app)
    yield RecordIndexer()


@pytest.fixture(scope="session")
def test_data():
    """Load test records."""
    path = "data/testrecords.json"
    with open(join(dirname(__file__), path)) as fp:
        records = json.load(fp)
    yield records


@pytest.fixture()
def test_records(db, test_data):
    """Load test records."""
    result = []
    for r in test_data:
        result.append(create_record(r))
    db.session.commit()
    yield result


@pytest.fixture()
def indexed_records(search_class, indexer, test_records):
    """Get a function to wait for records to be flushed to index."""
    for pid, record in test_records:
        indexer.index_by_id(record.id)
    current_search.flush_and_refresh(index=search_class.Meta.index)
    yield test_records


@pytest.fixture(scope="session")
def test_patch():
    """A JSON patch."""
    yield [{"op": "replace", "path": "/year", "value": 1985}]
