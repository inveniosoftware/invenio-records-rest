{% include 'misc/header.py' %}

"""Record serializers.

Serialization or "dumping" of internal application objects refers to producing
the formatted result, which can be stored in persistent storage or sent through
a communication link.
Invenio-Records-REST contains several tools for this process. A basic
serializer is the JSONSerializer which produces JSON formatted outputs.
The schema containing the record structure is passed as a parameter in
the provided json_v1 instance.

Also, there are different serializers defined for output of individual record
requests (json_v1_response) and search results (json_v1_search), as the
internal objects may not have indentical structures.
For more information on serializers please see
https://invenio-records-rest.readthedocs.io/en/latest/usage.html#serialization/
.
"""

from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from ..marshmallow import RecordSchemaV1

# Serializers
# ===========
json_v1 = JSONSerializer(RecordSchemaV1, replace_refs=True)

# Records-REST serializers
# ========================
# JSON record serializer for individual records.
json_v1_response = record_responsify(json_v1, 'application/json')
# JSON record serializer for search results.
json_v1_search = search_responsify(json_v1, 'application/json')

__all__ = (
    'json_v1',
    'json_v1_response',
    'json_v1_search',
)
