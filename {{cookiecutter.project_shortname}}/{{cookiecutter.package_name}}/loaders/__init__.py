from .json import json_patch_loader, marshmallow_loader
from .schemas import MetadataSchemaV1

# Loaders
# =======

# It uses the same schema as for the response serializers just for simplicity.
json_v1 = marshmallow_loader(MetadataSchemaV1)
json_patch_v1 = json_patch_loader

__all__ = (
    'json_v1',
    'json_patch_loader',
)
