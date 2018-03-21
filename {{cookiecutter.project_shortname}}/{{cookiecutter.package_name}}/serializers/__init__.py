"""Record serializers."""

from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from .json import JSONSerializer
from .schemas import RecordSchemaV1

# Serializers
# ===========
json_v1 = JSONSerializer(RecordSchemaV1, replace_refs=True)

# Records-REST serializers
# ========================
# JSON record serializer for individual records.
json_v1_response = record_responsify(json_v1, 'application/json')
# JSON record serializer for search results.
json_v1_search = search_responsify(json_v1, 'application/json')
