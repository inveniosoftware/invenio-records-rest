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
    $ flask -a app.py fixture records
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
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_cli import FlaskCLI
from invenio_db import InvenioDB, db
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_rest import InvenioREST

from invenio_records_rest import InvenioRecordsREST


# create application's instance directory. Needed for this example only.
current_dir = os.path.dirname(os.path.realpath(__file__))
instance_dir = os.path.join(current_dir, 'app_instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# Create Flask application
app = Flask(__name__, instance_path=instance_dir)
app.config.update(
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND="memory",
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND="cache",
    # No permission checking
    RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
    RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
    RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
    RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
)
FlaskCLI(app)
FlaskCeleryExt(app)
InvenioDB(app)
InvenioREST(app)
InvenioPIDStore(app)
InvenioRecords(app)
InvenioRecordsREST(app)


@app.cli.group()
def fixtures():
    """Command for working with test data."""


@fixtures.command()
def records():
    """Load test data fixture."""
    import uuid
    from invenio_records.api import Record
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus

    # Record 1 - Live record
    with db.session.begin_nested():
        rec_uuid = uuid.uuid4()
        pid1 = PersistentIdentifier.create(
            'recid', '1', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({'title': 'Registered '}, id_=rec_uuid)

        # Record 2 - Deleted PID with record
        rec_uuid = uuid.uuid4()
        pid = PersistentIdentifier.create(
            'recid', '2', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({'title': 'Live '}, id_=rec_uuid)
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
