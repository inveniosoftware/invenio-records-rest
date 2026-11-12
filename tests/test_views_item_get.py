# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Get record tests."""

import pytest
from flask import current_app, url_for
from helpers import get_json, record_url, to_relative_url


def test_item_get(app, test_records):
    """Test record retrieval."""
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200
        assert res.cache_control.no_cache
        assert res.headers["ETag"].startswith('"{}-'.format(record.revision_id))
        assert "Accept" in res.vary

        # Check metadata
        data = get_json(res)
        for k in ["id", "created", "updated", "metadata", "links"]:
            assert k in data

        assert data["id"] == pid.pid_value
        assert data["metadata"] == record.dumps()

        # Check self links
        client.get(to_relative_url(data["links"]["self"]))
        assert res.status_code == 200
        assert data == get_json(res)


def test_item_get_etag(app, test_records):
    """Test VALID record get request (GET .../records/<record_id>)."""
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid))
        assert res.status_code == 200
        assert res.cache_control.no_cache

        etag = res.headers["ETag"]
        last_modified = res.headers["Last-Modified"]

        # Test request via etag
        res = client.get(record_url(pid), headers={"If-None-Match": etag})
        assert res.status_code == 304
        assert res.cache_control.no_cache

        # Test request via last-modified.
        res = client.get(record_url(pid), headers={"If-Modified-Since": last_modified})
        assert res.status_code == 304
        assert res.cache_control.no_cache


def xml_record(*args, **kwargs):
    """Test serializer."""
    return current_app.response_class("<record/>", content_type="application/xml")


@pytest.mark.parametrize(
    "app",
    [
        dict(
            endpoint=dict(
                record_serializers={
                    "application/json": (
                        "invenio_records_rest.serializers:json_v1_response"
                    ),
                    "application/xml": "test_views_item_get:xml_record",
                },
                default_media_type="application/json",
            ),
        )
    ],
    indirect=["app"],
    scope="function",
)
def test_item_get_etag_per_representation(app, test_records):
    """Test conditional requests do not mix up the representations of a record.

    A browser revalidates its cached representation with its ETag and its
    Last-Modified date, even for a request asking for another representation.
    """
    with app.test_client() as client:
        pid, record = test_records[0]

        res = client.get(record_url(pid), headers={"Accept": "application/json"})
        json_etag = res.headers["ETag"]
        conditions = {
            "If-None-Match": json_etag,
            "If-Modified-Since": res.headers["Last-Modified"],
        }

        res = client.get(
            record_url(pid), headers={"Accept": "application/xml", **conditions}
        )
        assert res.status_code == 200
        assert res.content_type == "application/xml"
        assert res.headers["ETag"] != json_etag

        res = client.get(
            record_url(pid), headers={"Accept": "application/json", **conditions}
        )
        assert res.status_code == 304
        assert res.headers["ETag"] == json_etag
        assert "Accept" in res.vary


def test_item_get_norecord(app, test_records):
    """Test INVALID record get request (GET .../records/<record_id>)."""
    with app.test_client() as client:
        # check that GET with non existing id will return 404
        res = client.get(
            url_for("invenio_records_rest.recid_item", pid_value="0"),
        )
        assert res.status_code == 404


def test_item_get_invalid_mimetype(app, test_records):
    """Test invalid mimetype returns 406."""
    with app.test_client() as client:
        pid, record = test_records[0]

        # Check that GET with non accepted format will return 406
        res = client.get(record_url(pid), headers=[("Accept", "video/mp4")])
        assert res.status_code == 406
