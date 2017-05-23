# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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


"""Link factory tests."""

from __future__ import absolute_import, print_function

from helpers import create_record

from invenio_records_rest.links import default_links_factory_with_additional


def test_default_links_factory_with_additional(app, db):
    """Test links factory with additional links."""
    pid, record = create_record({'title': 'test'})
    with app.test_request_context('/records/1'):
        link_factory = default_links_factory_with_additional(
            dict(test_link='{scheme}://{host}/{pid.pid_value}'))
        links = link_factory(pid)
        assert links['test_link'] == 'http://localhost:5000/1'
