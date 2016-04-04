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

"""Auto-index records metadata."""

from collections import namedtuple

import flask
import pytz
from elasticsearch_dsl import Q
from flask import current_app
from flask_security import current_user
from flask_sqlalchemy import before_models_committed, models_committed
from invenio_access.models import ActionUsers
from invenio_db import db
from invenio_records.models import RecordMetadata
from invenio_records.permissions import records_read_all
from invenio_search import current_search_client

IndexedRecord = namedtuple('IndexedRecord', ['body', 'version'])


def _index_search_record(record):
    """Index the given record."""
    user_permissions = db.session.query(ActionUsers).filter(
        ActionUsers.argument == str(record.id)).filter(
        ActionUsers.action == records_read_all.value).all()
    record_json = {
        '_access': {
            'include_users': [perm.user_id for perm in user_permissions
                              if not perm.exclude],
            'exclude_users': [perm.user_id for perm in user_permissions
                              if perm.exclude],
            'public': 1 if len(user_permissions) == 0 else 0
        },
        '_created': pytz.utc.localize(record.created).isoformat()
        if record.created else None,
        '_updated': pytz.utc.localize(record.updated).isoformat()
        if record.updated else None,
    }
    if record.json is not None:
        record_json.update(record.json)
    return IndexedRecord(
        body=record_json,
        version=record.version_id - 1 if record.version_id else 0,
    )


def register_record_modification(sender, changes):
    """Example handler for indexing access restricted record metadata."""
    records_to_index = flask.g.get('invenio_search_records_to_index', dict())
    records_to_delete = flask.g.get('invenio_search_records_to_delete', set())
    for obj, change in changes:
        if isinstance(obj, RecordMetadata):
            if change in ('insert', 'update'):
                records_to_index[str(obj.id)] = _index_search_record(obj)
            elif change in ('delete'):
                records_to_delete.add(str(obj.id))
        elif (isinstance(obj, ActionUsers) and
                obj.action == records_read_all.value):
            # check that we didn't already register this record
            record = db.session.query(RecordMetadata).filter(
                RecordMetadata.id == obj.argument).one_or_none()
            if record is not None:
                records_to_index[str(record.id)] = \
                    _index_search_record(record)

    flask.g.invenio_search_records_to_index = records_to_index
    flask.g.invenio_search_records_to_delete = records_to_delete


def index_record_modification(sender, changes):
    """Reset the set of processed records for the next session."""
    records_to_index = flask.g.get('invenio_search_records_to_index', dict())
    records_to_delete = flask.g.get('invenio_search_records_to_delete', set())
    es_index = current_app.config["RECORDS_REST_DEFAULT_SEARCH_INDEX"]
    for id in records_to_index:
        if id not in records_to_delete:
            current_search_client.index(
                index=es_index,
                doc_type='testrecord-v1.0.0',
                id=id,
                body=records_to_index[id].body,
                version=records_to_index[id].version,
                version_type='external_gte',
            )
    for id in records_to_delete:
        current_search_client.delete(
            index=es_index,
            doc_type='testrecord-v1.0.0',
            id=id,
        )

    flask.g.invenio_search_records_to_index = dict()
    flask.g.invenio_search_records_to_delete = set()


def filter_record_access_query_enhancer():
    """Enhance query with user authentication rules."""
    if not current_user.is_authenticated:
        return Q('match', **{'_access.public': 1})
    return Q(
        'match', **{'_access.include_users': current_user.id}
    ) & ~Q(
        'match', **{'_access.exclude_users': current_user.id}
    )


def prepare_indexing(app):
    """Prepare indexing."""
    before_models_committed.connect(register_record_modification)
    models_committed.connect(index_record_modification)
