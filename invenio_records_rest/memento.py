# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Support for Memento response."""

from __future__ import absolute_import, print_function

from flask import after_this_request, request
from invenio_records.api import Record
from link_header import Link, LinkHeader
from werkzeug.http import http_date, parse_date


def get_memento(record, accept_datetime):
    """Return revision of the record for given datetime."""
    if accept_datetime >= record.updated:
        return record
    for revision in reversed(record.revisions):
        updated = revision.updated.replace(microsecond=0)
        if updated <= accept_datetime:
            return revision
    return revision


class MementoRecord(Record):
    """Implement basic Memento protocol.

    The original resource acts as its own TimeGate without distict Memento
    URI (see section 4.1.3).
    """

    @classmethod
    def get_record(cls, *args, **kwargs):
        """Return record object and enhance response."""
        record = super(MementoRecord, cls).get_record(*args, **kwargs)

        if request.method in ('GET', 'HEAD'):
            if 'Accept-Datetime' in request.headers:
                memento = get_memento(record, parse_date(
                    request.headers['Accept-Datetime']
                ))

                @after_this_request
                def memento_datetime(response):
                    """Add Memento-Datetime header."""
                    response.headers['Memento-Datetime'] = http_date(
                        memento.updated
                    )
                    response.headers['Vary'] = 'accept-datetime, accept'
                    response.headers['Link'] = LinkHeader([
                        Link(request.url, rel='original timegate')
                    ])
                    return response
                return memento
        return record
