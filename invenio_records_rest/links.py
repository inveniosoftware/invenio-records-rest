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

"""Links for record serialization."""

from flask import url_for

from .proxies import current_records_rest


def default_links_factory(pid):
    """Factory for record links generation.

    :param pid: A Persistent Identifier instance.
    :returns: Dictionary containing a list of useful links for the record.
    """
    endpoint = '.{0}_item'.format(
        current_records_rest.default_endpoint_prefixes[pid.pid_type])
    links = dict(self=url_for(endpoint, pid_value=pid.pid_value,
                 _external=True))
    return links
