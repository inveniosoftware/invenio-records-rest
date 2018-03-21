from ..serializes.schemas import RecordSchemaV1
from .json import json_patch_loader, marshmallow_loader

# Loaders
# =======

# It uses the same schema as for the response serializers just for simplicity.
json_v1 = marshmallow_loader(RecordSchemaV1)
json_patch_v1 = json_patch_loader
