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

"""Mixin helper class for preprocessing records and search results."""

from __future__ import absolute_import, print_function

import copy

import pytz


class PreprocessorMixin(object):
    """Base class for serializers."""

    def __init__(self, replace_refs=False):
        """."""
        self.replace_refs = replace_refs

    def preprocess_record(self, pid, record, links_factory=None):
        """Prepare a record and persistent identifier for serialization."""
        links_factory = links_factory or (lambda x: dict())
        metadata = copy.deepcopy(record.replace_refs()) if self.replace_refs \
            else record.dumps()
        return dict(
            pid=pid,
            metadata=metadata,
            links=links_factory(pid),
            revision=record.revision_id,
            created=(pytz.utc.localize(record.created).isoformat()
                     if record.created else None),
            updated=(pytz.utc.localize(record.updated).isoformat()
                     if record.updated else None),
        )

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None):
        """Prepare a record hit from Elasticsearch for serialization."""
        links_factory = links_factory or (lambda x: dict())
        record = dict(
            pid=pid,
            metadata=record_hit['_source'],
            links=links_factory(pid),
            revision=record_hit['_version'],
            created=None,
            updated=None,
        )
        # Move created/updated attrs from source to object.
        for key in ['_created', '_updated']:
            if key in record['metadata']:
                record[key[1:]] = record['metadata'][key]
                del record['metadata'][key]
        return record
