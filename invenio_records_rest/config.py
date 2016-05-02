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

"""Invenio-Records-REST configuration."""

from __future__ import absolute_import, print_function

from flask import request
from invenio_search import RecordsSearch

from .facets import terms_filter
from .utils import check_elasticsearch, deny_all


def _(x):
    return x

RECORDS_REST_ENDPOINTS = dict(
    recid=dict(
        pid_type='recid',
        pid_minter='recid',
        pid_fetcher='recid',
        search_class=RecordsSearch,
        search_index=None,
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/records/',
        item_route='/records/<pid(recid):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
    ),
)

RECORDS_REST_DEFAULT_LOADERS = {
    'application/json': lambda: request.get_json(),
    'application/json-patch+json': lambda: request.get_json(force=True),
}
"""Default data loaders per request mime type.

This option can be overritten in each REST endpoint as follows::

    {
        "recid": {
            ...
            "record_loaders": {
                "aplication/json": "mypackage.utils:myloader"
            },
            ...
        }
    }

"""

RECORDS_REST_SORT_OPTIONS = dict(
    records=dict(
        bestmatch=dict(
            title=_('Best match'),
            fields=['_score'],
            default_order='desc',
            order=1,
        ),
        mostrecent=dict(
            title=_('Most recent'),
            fields=['created_date'],
            default_order='desc',
            order=2,
        ),
    )
)
"""Sort options for default sorter factory.

The structure of the dictionary is as follows::

    {
        "<index or index alias>": {
            "fields": ["<search_field>", "<search_field>", ...],
            "title": "<title displayed to end user in search-ui>",
            "default_order": "<default sort order in search-ui>",
        }
    }

Each search field can be either:

- A string of the form ``"<field name>"`` (ascending) or ``"-<field name>"``
  (descending).
- A dictionary with Elasicsearch sorting syntax (e.g.
  ``{"price" : {"order" : "asc", "mode" : "avg"}}``).
- A callable taking one boolean parameter (``True`` for ascending and ``False``
  for descending) and returning a dictionary like above. This is useful if you
  need to extract extra sorting parameters (e.g. for geo location searches).
"""

RECORDS_REST_DEFAULT_SORT = dict(
    records=dict(
        query='bestmatch',
        noquery='mostrecent',
    )
)
"""Default sort option per index with/without query string."""

RECORDS_REST_FACETS = dict(
    records=dict(
        aggs=dict(
            type=dict(terms=dict(field='type'))
        ),
        post_filters=dict(
            type=terms_filter('type'),
        )
    )
)
"""Facets per index for the default facets factory.

The structure of the dictionary is as follows::

    {
        "<index or index alias>": {
            "aggs": {
                "<key>": <aggregation definition>,
                ...
            }
            "filters": {
                "<key>": <filter func>,
                ...
            }
            "post_filters": {
                "<key>": <filter func>,
                ...
            }
        }
    }
"""

RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY = deny_all
RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY = check_elasticsearch
RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY = deny_all
RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY = deny_all
