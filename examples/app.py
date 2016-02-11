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


"""Minimal Flask application example for development.

For this example the access control is disabled.

Run example development server:

.. code-block:: console

    $ cd examples
    $ flask -a app.py db init
    $ flask -a app.py db create
    $ flask -a app.py fixtures records
    $ flask -a app.py --debug run

Try to get some records:

.. code-block:: console

    $ curl -XGET http://localhost:5000/records/1
    $ curl -XGET http://localhost:5000/records/2
    $ curl -XGET http://localhost:5000/records/3
    $ curl -XGET http://localhost:5000/records/4
    $ curl -XGET http://localhost:5000/records/5
    $ curl -XGET http://localhost:5000/records/6
    $ curl -XGET http://localhost:5000/records/7

Then search for existing records:

    $ curl -v -XGET 'http://localhost:5000/records/?size=3'
    $ curl -v -XGET 'http://localhost:5000/records/?size=2&page=3'
    $ curl -v -XGET 'http://localhost:5000/records/?q=awesome'
    $ curl -v -XGET 'http://localhost:5000/records/?sort=-control_number'

View options about the endpoint:

    $ curl -v -XGET 'http://localhost:5000/records/_options'
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_cli import FlaskCLI
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, current_search_client

from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.config import RECORDS_REST_ENDPOINTS

# create application's instance directory. Needed for this example only.
current_dir = os.path.dirname(os.path.realpath(__file__))
instance_dir = os.path.join(current_dir, 'app_instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# Create Flask application
index_name = 'records-rest-example-app'
app = Flask(__name__, instance_path=instance_dir)
app.config.update(
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND='memory',
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND='cache',
    # No permission checking
    RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
    RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
    RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
    RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    INDEXER_DEFAULT_INDEX=index_name,
)
app.config['RECORDS_REST_ENDPOINTS'] = RECORDS_REST_ENDPOINTS
app.config['RECORDS_REST_ENDPOINTS']['recid']['search_index'] = index_name
app.config['RECORDS_REST_SORT_OPTIONS'] = {
    index_name: {
        'title': dict(fields=['title'], title='Title', order=1),
        'control_number': dict(
            fields=['control_number'], title='Record identifier', order=1),
    }
}
FlaskCLI(app)
FlaskCeleryExt(app)
InvenioDB(app)
InvenioREST(app)
InvenioPIDStore(app)
InvenioRecords(app)
InvenioSearch(app)
InvenioIndexer(app)
InvenioRecordsREST(app)

# A few documents which will be added in order to make search interesting
record_examples = [{
    'title': 'Awesome meeting report',
    'description': 'Notes of the last meeting.',
    'participants': 42,
}, {
    'title': 'Furniture order',
    'description': 'Tables for the meeting room.',
}]
record_examples += [{
    'title': 'LHC experiment {}'.format(idx),
    'description': 'Data from experiment {}.'.format(idx)
} for idx in range(20)]


@app.cli.group()
def fixtures():
    """Command for working with test data."""


@fixtures.command()
def records():
    """Load test data fixture."""
    import uuid
    from invenio_records.api import Record
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus

    current_search_client.indices.delete(
        index=index_name,
        ignore=[400, 404],
    )
    current_search_client.indices.create(
        index=index_name,
    )
    indexer = RecordIndexer()
    index_queue = []

    # Record 1 - Live record
    with db.session.begin_nested():
        rec_uuid = uuid.uuid4()
        pid1 = PersistentIdentifier.create(
            'recid', '1', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({
            'title': 'Registered',
            'description': 'This is an awesome description',
            # "mint" the record as recid minter does
            'control_number': 1
        }, id_=rec_uuid)
        index_queue.append(pid1.object_uuid)

        # Record 2 - Deleted PID with record
        rec_uuid = uuid.uuid4()
        pid = PersistentIdentifier.create(
            'recid', '2', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({
            'title': 'Live ',
            'control_number': 2
        }, id_=rec_uuid)
        pid.delete()

        # Record 3 - Deleted PID without a record
        PersistentIdentifier.create(
            'recid', '3', status=PIDStatus.DELETED)

        # Record 4 - Registered PID without a record
        PersistentIdentifier.create(
            'recid', '4', status=PIDStatus.REGISTERED)

        # Record 5 - Redirected PID
        pid = PersistentIdentifier.create(
            'recid', '5', status=PIDStatus.REGISTERED)
        pid.redirect(pid1)

        # Record 6 - Redirected non existing endpoint
        doi = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.REGISTERED)
        pid = PersistentIdentifier.create(
            'recid', '6', status=PIDStatus.REGISTERED)
        pid.redirect(doi)

        # Record 7 - Unregistered PID
        PersistentIdentifier.create(
            'recid', '7', status=PIDStatus.RESERVED)

        for rec_idx in range(len(record_examples)):
            rec_uuid = uuid.uuid4()
            rec_pid = 8 + rec_idx
            pid1 = PersistentIdentifier.create(
                'recid', str(rec_pid), object_type='rec', object_uuid=rec_uuid,
                status=PIDStatus.REGISTERED)
            # "mint" the record as recid minter does
            record = dict(record_examples[rec_idx])
            record['control_number'] = rec_pid
            # create the record
            Record.create(record, id_=rec_uuid)
            index_queue.append(rec_uuid)
    db.session.commit()

    for i in index_queue:
        indexer.index_by_id(i)
