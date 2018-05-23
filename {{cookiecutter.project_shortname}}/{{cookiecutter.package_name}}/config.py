{% include 'misc/header.py' %}
"""{{ cookiecutter.description }}"""

from invenio_indexer.api import RecordIndexer
from invenio_search import RecordsSearch

# TODO: update your instance configuration
# from invenio_records_rest.config import RECORDS_REST_ENDPOINTS
# from {{ cookiecutter.package_name }}.config import {{ cookiecutter.package_name | upper }}_RECORDS_REST_ENDPOINTS
# RECORDS_REST_ENDPOINTS.update({{ cookiecutter.package_name | upper }}_RECORDS_REST_ENDPOINTS)

RECORDS_REST_ENDPOINTS = {
    '{{ cookiecutter.pid_name}}':
    dict(
        pid_type='recid',
        pid_minter='recid',
        pid_fetcher='recid',
        default_endpoint_prefix=True,
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index='records',
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
                                 ':json_v1'),
            'application/json-patch+json': ('{{ cookiecutter.package_name}}.'
                                            'loaders:json_patch_v1')
        },
        list_route='/records/',
        item_route='/records/<pid(recid):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
}


PIDSTORE_RECID_FIELD = '{{ cookiecutter.pid_name }}'

{{ cookiecutter.package_name | upper }}_ENDPOINTS_ENABLED = True
