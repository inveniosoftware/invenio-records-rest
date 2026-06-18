# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-FileCopyrightText: 2026 RERO.
# SPDX-License-Identifier: MIT

"""Record PUT tests."""

import json

import mock
import pytest
from conftest import IndexFlusher
from helpers import _mock_validate_fail, assert_hits_len, get_json, record_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError


@pytest.mark.parametrize(
    "content_type", ["application/json", "application/json;charset=utf-8"]
)
def test_valid_put(app, search, test_records, content_type, search_url, search_class):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [("Accept", "application/json"), ("Content-Type", content_type)]

    pid, record = test_records[0]

    record["year"] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
        assert res.status_code == 200

        # Check that the returned record matches the given data
        assert get_json(res)["metadata"]["year"] == 1234
        IndexFlusher(search_class).flush_and_wait()
        res = client.get(search_url, query_string={"year": 1234})
        assert_hits_len(res, 1)
        # Retrieve record via get request
        assert get_json(client.get(url))["metadata"]["year"] == 1234


@pytest.mark.parametrize(
    "content_type", ["application/json", "application/json;charset=utf-8"]
)
def test_valid_put_etag(
    app, search, test_records, content_type, search_url, search_class
):
    """Test concurrency control with etags."""
    HEADERS = [("Accept", "application/json"), ("Content-Type", content_type)]

    pid, record = test_records[0]

    record["year"] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(
            url,
            data=json.dumps(record.dumps()),
            headers={
                "Content-Type": "application/json",
                "If-Match": '"{0}"'.format(record.revision_id),
            },
        )
        assert res.status_code == 200
        assert get_json(client.get(url))["metadata"]["year"] == 1234

        IndexFlusher(search_class).flush_and_wait()
        res = client.get(search_url, query_string={"year": 1234})
        assert_hits_len(res, 1)


@pytest.mark.parametrize(
    "content_type", ["application/json", "application/json;charset=utf-8"]
)
def test_put_on_deleted(
    app, db, search, test_data, content_type, search_url, search_class
):
    """Test putting to a deleted record."""
    with app.test_client() as client:
        HEADERS = [("Accept", "application/json"), ("Content-Type", content_type)]
        HEADERS.append(("Content-Type", content_type))

        # Create record
        res = client.post(search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 201

        url = record_url(get_json(res)["id"])
        assert client.delete(url).status_code == 204
        IndexFlusher(search_class).flush_and_wait()
        res = client.get(search_url, query_string={"title": test_data[0]["title"]})
        assert_hits_len(res, 0)

        res = client.put(url, data="{}", headers=HEADERS)
        assert res.status_code == 410


@pytest.mark.parametrize("charset", ["", ";charset=utf-8"])
def test_invalid_put(app, search, test_records, charset, search_url):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    HEADERS = [
        ("Accept", "application/json"),
        ("Content-Type", "application/json{0}".format(charset)),
    ]

    pid, record = test_records[0]

    record["year"] = 1234
    test_data = record.dumps()

    with app.test_client() as client:
        url = record_url(pid)

        # Non-existing record
        res = client.put(record_url("0"), data=json.dumps(test_data), headers=HEADERS)
        assert res.status_code == 404
        res = client.get(search_url, query_string={"year": 1234})
        assert_hits_len(res, 0)

        # Invalid accept mime type.
        headers = [
            ("Content-Type", "application/json{0}".format(charset)),
            ("Accept", "video/mp4"),
        ]
        res = client.put(url, data=json.dumps(test_data), headers=headers)
        assert res.status_code == 406

        # Invalid content type
        headers = [
            ("Content-Type", "video/mp4{0}".format(charset)),
            ("Accept", "application/json"),
        ]
        res = client.put(url, data=json.dumps(test_data), headers=headers)
        assert res.status_code == 415

        # Invalid JSON
        res = client.put(url, data="{invalid-json", headers=HEADERS)
        assert res.status_code == 400

        # Invalid ETag
        res = client.put(
            url,
            data=json.dumps(test_data),
            headers={
                "Content-Type": "application/json{0}".format(charset),
                "If-Match": '"2"',
            },
        )
        assert res.status_code == 412


@mock.patch("invenio_records.api.Record.commit", _mock_validate_fail)
@pytest.mark.parametrize(
    "content_type", ["application/json", "application/json;charset=utf-8"]
)
def test_validation_error(app, test_records, content_type):
    """Test when record validation fail."""
    HEADERS = [("Accept", "application/json"), ("Content-Type", content_type)]

    pid, record = test_records[0]

    record["year"] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
        assert res.status_code == 400


def test_put_stale_data_returns_409(app, db, test_records):
    """PUT on a stale record returns 409, not 500 PIDResolveRESTError.

    SQLAlchemy optimistic-locking raises StaleDataError when two concurrent
    requests read revision N and the second one tries to commit after the first
    already bumped the revision to N+1.  The fix moves the return inside put()
    outside pass_record's try/except so the error is handled locally as a 409.
    """
    HEADERS = [("Accept", "application/json"), ("Content-Type", "application/json")]
    pid, record = test_records[0]

    with mock.patch(
        "invenio_db.db.session.commit", side_effect=StaleDataError("stale")
    ):
        with app.test_client() as client:
            url = record_url(pid)
            res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
            assert res.status_code == 409


def test_pass_record_does_not_swallow_handler_sqlalchemy_errors(app, db, test_records):
    """SQLAlchemyError from the handler must not be caught by pass_record.

    Before the fix, pass_record wrapped the handler call inside the
    try/except SQLAlchemyError used for PID resolution, so any database error
    raised inside put() (e.g. IntegrityError) would be silently re-raised as a
    PIDResolveRESTError(500) with a misleading "PID could not be resolved"
    message.  After the fix, such errors propagate unmodified.
    """
    HEADERS = [("Accept", "application/json"), ("Content-Type", "application/json")]
    pid, record = test_records[0]

    with mock.patch(
        "invenio_db.db.session.commit", side_effect=SQLAlchemyError("db error")
    ):
        with app.test_client() as client:
            url = record_url(pid)
            # TESTING=True propagates unhandled exceptions; catch at the
            # test level and verify it is the original SQLAlchemyError, NOT
            # a PIDResolveRESTError swallowing it.
            with pytest.raises(SQLAlchemyError):
                client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
