# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow based DublinCore serializer for records."""

from __future__ import absolute_import, print_function

import csv
import tempfile

from .base import PreprocessorMixin, SerializerMixinInterface
from .marshmallow import MarshmallowMixin


class CSVSerializer(SerializerMixinInterface, MarshmallowMixin,
                    PreprocessorMixin):
    """CSV serializer for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    def __init__(self, *args, **kwargs):
        """Initialize CSVSerializer.

        :param csv_excluded_fields: list of complete paths of the fields that
                                    should be excluded from the final output
        :param header_separator: separator that should be used when flattening
                                 nested dictionary keys
        """
        self.csv_excluded_fields = kwargs.pop("csv_excluded_fields", [])
        self.header_separator = kwargs.pop("header_separator", "_")
        super(CSVSerializer, self).__init__(*args, **kwargs)

    def serialize(self, pid, record, links_factory=None):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        record = self.process_dict(
            self.transform_record(pid, record, links_factory))

        return self.format_csv([record])

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        records = []
        for hit in search_result['hits']['hits']:
            processed_hit = self.transform_search_hit(
                pid_fetcher(hit['_id'], hit['_source']),
                hit,
                links_factory=item_links_factory,
            )
            records.append(self.process_dict(processed_hit))

        return self.format_csv(records)

    def format_csv(self, records):
        """Format list of flattened dictionaries into CSV format."""
        # build a list of all the headers from all the rows
        # and remove any duplicates with a set
        headers = sorted(set([key for record in records for key in record]))

        temp_file = tempfile.NamedTemporaryFile(suffix='.csv',
                                                prefix='export',
                                                mode='w+',
                                                delete=False)

        with temp_file as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for record in records:
                writer.writerow(record)
            csv_file.seek(0)
            return csv_file.read()

    def process_dict(self, dictionary):
        """Returns a flattened dictionary as a string."""
        flattened = {}

        self.flatten(dictionary, flattened)

        for path in self.csv_excluded_fields:
            for key in list(flattened.keys())[:]:
                if path in key:
                    del flattened[key]

        return flattened

    def flatten(self, elem, flattened, parent_key=''):
        """Flattens nested dictionaries."""
        if isinstance(elem, dict):
            for key in elem:
                self.flatten(elem[key], flattened,
                             parent_key + key + self.header_separator)
        elif isinstance(elem, list):
            for index, item in enumerate(elem):
                self.flatten(item, flattened,
                             parent_key + str(index) + self.header_separator)
        else:
            flattened[parent_key[0:-1]] = elem
