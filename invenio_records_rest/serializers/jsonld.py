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

"""Marshmallow based JSON serializer for records."""

from __future__ import absolute_import, print_function

import copy

from flask import request
from marshmallow import Schema, fields
from marshmallow.decorators import post_dump
from pyld import jsonld

from .json import JSONSerializer


class RecordMetadataOnlySchema(Schema):
    """Schema which extracts the metadata only."""

    @post_dump
    def post_dump(self, obj):
        """Get metadata only from the record."""
        return obj.get('metadata', {})


class JSONLDSerializer(JSONSerializer):
    """JSON-LD serializer for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    def __init__(self, context, schema_class=RecordMetadataOnlySchema,
                 expanded=True, replace_refs=False):
        """Initialize record.

        :param context: JSON-LD context.
        :param schema_class: Marshmallow schema.
        :param expanded: expanded form, compacted else.
        :param replace_refs: replace the ``$ref`` keys within the JSON.
        """
        self.context = context
        self._expanded = expanded
        super(JSONLDSerializer, self).__init__(
            schema_class=schema_class, replace_refs=replace_refs
        )

    @property
    def expanded(self):
        """Get JSON-LD expanded state."""
        # Ensure we can run outside a application/request context.
        if request:
            if 'expanded' in request.args:
                return True
            elif 'compacted' in request.args:
                return False
        return self._expanded

    def dump(self, obj):
        """Compact JSON according to context."""
        rec = copy.deepcopy(super(JSONLDSerializer, self).dump(obj))
        rec.update(self.context)
        compacted = jsonld.compact(rec, self.context)
        if not self.expanded:
            return compacted
        else:
            return jsonld.expand(compacted)[0]
