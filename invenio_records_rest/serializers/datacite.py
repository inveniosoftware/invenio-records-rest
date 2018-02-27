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

"""Marshmallow based DataCite serializer for records."""

from __future__ import absolute_import, print_function

from datacite import schema31, schema40, schema41
from invenio_records.api import Record
from lxml import etree
from lxml.builder import E

from .base import PreprocessorMixin
from .marshmallow import MarshmallowMixin


class BaseDataCiteSerializer(MarshmallowMixin, PreprocessorMixin):
    """Marshmallow based DataCite serializer for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    schema = None
    """Class variable to define which schema use."""
    version = None
    """Class variable to tell the version of the schema."""

    def serialize(self, pid, record, links_factory=None):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        return self.schema.tostring(
            self.transform_record(pid, record, links_factory))

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        records = []
        for hit in search_result['hits']['hits']:
            records.append(self.schema.tostring(self.transform_search_hit(
                pid_fetcher(hit['_id'], hit['_source']),
                hit,
                links_factory=item_links_factory,
            )))

        return "\n".join(records)

    def serialize_oaipmh(self, pid, record):
        """Serialize a single record for OAI-PMH."""
        obj = self.transform_record(pid, record['_source']) \
            if isinstance(record['_source'], Record) \
            else self.transform_search_hit(pid, record)

        return self.schema.dump_etree(obj)


class DataCite31Serializer(BaseDataCiteSerializer):
    """Marshmallow DataCite serializer v3.1 for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    schema = schema31
    """Class variable to define which schema use."""
    version = '3.1'
    """Class variable to tell the version of the schema."""


class DataCite40Serializer(BaseDataCiteSerializer):
    """Marshmallow DataCite serializer v4.0 for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    schema = schema40
    """Class variable to define which schema use."""
    version = '4.0'
    """Class variable to tell the version of the schema."""


class DataCite41Serializer(BaseDataCiteSerializer):
    """Marshmallow DataCite serializer v4.1 for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    schema = schema41
    """Class variable to define which schema use."""
    version = '4.1'
    """Class variable to tell the version of the schema."""


class OAIDataCiteSerializer(object):
    """OAI DataCite serializer (only for OAI-PMH)."""

    def __init__(self, serializer=None, datacentre=None,
                 is_reference_quality='true'):
        """Initialize serializer."""
        self.serializer = serializer
        self.datacentre = datacentre
        self.is_reference_quality = is_reference_quality

    def serialize_oaipmh(self, pid, record):
        """Serialize a single record for OAI-PMH."""
        root = etree.Element(
            'oai_datacite',
            nsmap={
                None: 'http://schema.datacite.org/oai/oai-1.0/',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xml': 'xml',
            },
            attrib={
                '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
                'http://schema.datacite.org/oai/oai-1.0/ oai_datacite.xsd',
            }
        )

        root.append(E.isReferenceQuality(self.is_reference_quality))
        root.append(E.schemaVersion(self.serializer.version))
        root.append(E.datacentreSymbol(self.datacentre))
        root.append(E.payload(
            self.serializer.serialize_oaipmh(pid, record)
        ))

        return root
