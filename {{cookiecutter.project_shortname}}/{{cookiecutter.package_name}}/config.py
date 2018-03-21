{% include 'misc/header.py' %}
"""{{ cookiecutter.description }}"""

from invenio_indexer.api import RecordIndexer
from invenio_search import RecordsSearch

RECORDS_REST_ENDPOINTS = {
    '{{ cookiecutter.pid_name}}':
    dict(
        pid_type='recid',
        pid_minter='recid',
        pid_fetcher='recid',
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index=None,
        search_type=None,
        record_serializers={
            'application/json': ('{{ cookiecutter.package_name}}.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('{{ cookiecutter.package_name}}.serializers'
                                 ':json_v1_search'),
        },
        record_loaders={
            'application/json': ('{{ cookiecutter.package_name }}.loaders'
                                 ':json_v1_loader'),
            'application/json-patch+json': ('{{ cookiecutter.package_name}}.'
                                            'loaders:json_patch_v1_loader')
        },
        list_route='/records/',
        item_route='/records/<pid(recid):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
}


PIDSTORE_RECID_FIELD = '{{ cookiecutter.pid_name }}'
