# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Record serialization."""

from ..schemas import RecordSchemaJSONV1
from .json import JSONSerializer
from .response import record_responsify, search_responsify

json_v1 = JSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_v1_response = record_responsify(json_v1, "application/json")
"""JSON response builder that uses the JSON v1 serializer."""

json_v1_search = search_responsify(json_v1, "application/json")
"""JSON search response builder that uses the JSON v1 serializer."""
