# SPDX-FileCopyrightText: 2015-2019 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Index prefixing tests."""

import json

import pytest
from conftest import IndexFlusher
from helpers import assert_hits_len, get_json, record_url
from invenio_search import current_search


@pytest.fixture(scope="module")
def app_config(app_config):
    """Prefix all the indices.

    Set for the whole module, so that the module-scoped ``search`` fixture
    creates the prefixed indices.
    """
    app_config["SEARCH_INDEX_PREFIX"] = "test-"
    return app_config


def test_index_creation(app, search, search_index_names):
    """Sanity check for index creation."""
    suffix = current_search.current_suffix
    es_aliases = search.indices.get_alias()
    # Keys are the indices
    assert search_index_names() == {
        "test-invenio-records-rest-testrecord{}".format(suffix),
    }

    aliases = set()
    for index_info in es_aliases.values():
        aliases |= set(index_info.get("aliases", {}).keys())
    assert aliases == {
        "test-invenio-records-rest",
        "test-invenio-records-rest-testrecord",
    }


def test_api_views(app, search_clear, db, test_data, search_url, search_class):
    """Test REST API views behavior."""
    suffix = current_search.current_suffix

    with app.test_client() as client:
        HEADERS = [
            ("Accept", "application/json"),
            ("Content-Type", "application/json"),
        ]

        # Create record
        res = client.post(search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        recid = get_json(res)["id"]
        assert res.status_code == 201

        # Flush and check indices
        IndexFlusher(search_class).flush_and_wait()
        result = search_clear.search(index="test-invenio-records-rest")
        assert len(result["hits"]["hits"]) == 1
        record_doc = result["hits"]["hits"][0]
        assert record_doc["_index"] == "test-invenio-records-rest-testrecord" + suffix

        # Fetch the record
        assert client.get(record_url(recid)).status_code == 200
        # Record shows up in search
        res = client.get(search_url)
        assert_hits_len(res, 1)

        # Delete the record
        res = client.delete(record_url(recid))
        IndexFlusher(search_class).flush_and_wait()
        result = search_clear.search(index="test-invenio-records-rest")
        assert len(result["hits"]["hits"]) == 0

        # Deleted record should return 410
        assert client.get(record_url(recid)).status_code == 410
        # Record doesn't show up in search
        res = client.get(search_url)
        assert_hits_len(res, 0)
