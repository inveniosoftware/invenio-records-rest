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

"""Invenio-Records-REST configuration loaders."""

from __future__ import absolute_import, print_function

from functools import partial
from collections import namedtuple

import six
from flask import _app_ctx_stack
from marshmallow import Schema, ValidationError, fields, post_load
from werkzeug.utils import cached_property
from invenio_records.api import Record
from invenio_search.api import RecordsSearch
from invenio_pidstore import current_pidstore
from invenio_pidstore.resolver import Resolver
from werkzeug.local import LocalProxy

from .links import default_links_factory
from .query import default_search_factory
from .utils import obj_or_import_string


class NoEndpointConfigError(Exception):
    """Exception raised when the endpoint configuration is no set."""


current_endpoint_config = LocalProxy(
    lambda: _current_endpoint_config())


def _current_endpoint_config():
    """Retrieve the current endpoint configuration.

    This requires that _invenio_records_rest_endpoint_config is currently set
    on the application context.
    """
    ctx = _app_ctx_stack.top
    if ctx is not None:
        if not hasattr(ctx, '_invenio_records_rest_endpoint_config'):
            raise NoEndpointConfigError('Endpoint configuration is not set.')
        return ctx._invenio_records_rest_endpoint_config
    raise NoEndpointConfigError('No application context.')


class EndpointConfig(namedtuple('RecordsRestEndpointConfig', [
    'list_route',
    'item_route',
    'pid_type',
    'pid_fetcher_name',
    'pid_minter_name',
    'search_index',
    'search_type',
    'search_class',
    'record_class',
    'record_serializers',
    'endpoint_record_loaders',
    'search_serializers',
    'search_factory',
    'max_result_window',
    'links_factory',
    'suggesters',
    'default_media_type',
    'read_permission_factory_imp',
    'create_permission_factory_imp',
    'update_permission_factory_imp',
    'delete_permission_factory_imp',
    'use_options_view',
    'resolver',
])):

    @cached_property
    def item_media_types(self):
        return self.record_serializers.keys()

    @cached_property
    def search_media_types(self):
        return self.search_serializers.keys()

    @cached_property
    def pid_minter(self):
        return current_pidstore.fetchers[self.pid_fetcher]

    @cached_property
    def pid_fetcher(self):
        return current_pidstore.fetchers[self.pid_fetcher]

    @cached_property
    def create_permission_factory(self):
        return self.create_permission_factory_imp or \
            current_records_rest.create_permission_factory

    @cached_property
    def update_permission_factory(self):
        return self.update_permission_factory_imp or \
            current_records_rest.update_permission_factory

    @cached_property
    def delete_permission_factory(self):
        return self.delete_permission_factory_imp or \
            current_records_rest.delete_permission_factory

    @cached_property
    def read_permission_factory(self):
        return self.read_permission_factory_imp or \
            current_records_rest.read_permission_factory

    @cached_property
    def record_loaders(self):
        return self.endpoint_record_loaders or \
            current_records_rest.loaders


class DictField(fields.Field):
    """Marshmallow dictionary field used when field names are unknown."""
    def __init__(self, key_field, nested_field, *args, **kwargs):
        fields.Field.__init__(self, *args, **kwargs)
        self.key_field = key_field
        self.nested_field = nested_field

    def _deserialize(self, value, attr, data):
        result = {}
        self._validate_missing(value)
        for key, subvalue in six.iteritems(value):
            deserialized_key = self.key_field.deserialize(key)
            deserialized_value = self.nested_field.deserialize(subvalue)
            result[deserialized_key] = deserialized_value
        return result


class CompletionConfig(fields.Field):
    """Record REST endpoint's completion suggester configuration schema."""

    field = fields.Str(required=True)

    context = fields.Str(required=False)

    size = fields.Integer(required=False)


class SuggesterConfig(fields.Field):
    """Record REST endpoint's suggester configuration schema."""

    completion = fields.Nested(CompletionConfig, required=False)


def deserialize_import_string_dict(obj):
    """Deserialize dicts of string->import_string."""
    if not isinstance(obj, dict):
        raise ValidationError(
            'Field "{}" should be an import string.'.format(attr),
            field_names=[attr]
        )
    return {key: obj_or_import_string(obj)
            for key, obj in six.iteritems(obj)}


class EndpointConfigSchema(Schema):
    """Record REST Endpoint Configuration schema."""

    @post_load
    def build_config(self, data):
        """Finish configuration loading."""
        search_class_kwargs = {}
        if data.get('search_index'):
            search_class_kwargs['index'] = data['search_index']
        else:
            data['search_index'] = data['search_class'].Meta.index

        if data.get('search_type'):
            search_class_kwargs['doc_type'] = data['search_type']
        else:
            data['search_type'] = data['search_class'].Meta.doc_types

        if search_class_kwargs:
            data['search_class'] = partial(data['search_class'],
                                           **search_class_kwargs)

        data['resolver'] = Resolver(
            pid_type=data['pid_type'],
            object_type='rec',
            getter=partial(data['record_class'].get_record, with_deleted=True))
        return EndpointConfig(**data)

    list_route = fields.Str(required=True)
    """Record listing URL route. Required."""

    item_route = fields.Str(required=True)
    """Record URL route (must include ``<pid_value>`` pattern). Required."""

    pid_type = fields.Str(required=True)
    """Persistent identifier type for endpoint. Required."""

    pid_minter_name = fields.Str(required=True, load_from='pid_minter')
    """Persistent identifier minting class."""

    pid_fetcher_name = fields.Str(required=True, load_from='pid_fetcher')
    """Class fetching records from their persistent identifier."""

    record_class = fields.Function(
        deserialize=obj_or_import_string,
        missing=lambda: Record)
    """Name of the record API class."""

    record_serializers = fields.Function(
        deserialize=deserialize_import_string_dict, required=True)
    """Serializers used for records."""

    endpoint_record_loaders = fields.Function(
        load_from='record_loaders', deserialize=deserialize_import_string_dict,
        missing=None)
    """Load record from Records REST request data."""

    links_factory = fields.Function(
        deserialize=obj_or_import_string,
        load_from='links_factory_imp', missing=lambda: default_links_factory
    )
    """Function creating the links for a serialized record."""

    search_class = fields.Function(
        deserialize=obj_or_import_string,
        missing=lambda: RecordsSearch)
    """Class building the final search query."""

    search_index = fields.Str(required=False, allow_none=True)
    """Name of the search index used when searching records."""

    search_type = fields.Str(required=False, allow_none=True)
    """Name of the search type used when searching records."""

    search_serializers = fields.Function(
        deserialize=deserialize_import_string_dict, required=True)
    """Serializers used for search results."""

    search_factory = fields.Function(
        load_from='search_factory_imp', deserialize=obj_or_import_string,
        missing=lambda: default_search_factory)
    """Function parsing the current request and configuring the search query.
    """

    max_result_window = fields.Integer(missing=10000)
    """Maximum number of results that Elasticsearch can
    provide for the given search index without use of scroll. This value
    should correspond to Elasticsearch
    ``index.max_result_window`` value
    for the index."""

    suggesters = DictField(fields.Str, SuggesterConfig, missing=None)

    default_media_type = fields.Str(required=True)
    """Default media type for both records and search."""

    read_permission_factory_imp = fields.Function(
        deserialize=obj_or_import_string, missing=None)
    """Import path to factory that creates a read permission object for a
    given record."""

    create_permission_factory_imp = fields.Function(
        deserialize=obj_or_import_string, missing=None)
    """Import path to factory that creates a create permission object for a
    given record."""

    update_permission_factory_imp = fields.Function(
        deserialize=obj_or_import_string, missing=None)
    """Import path to factory that creates an update permission object for a
    given record."""

    delete_permission_factory_imp = fields.Function(
        deserialize=obj_or_import_string, missing=None)
    """Import path to factory that creates a delete permission object for a
    given record."""

    use_options_view = fields.Boolean(missing=False)
    """Determines if a special option view should be
    installed."""
