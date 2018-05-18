"""Loaders.

This file contains sample loaders that can be used to
deserialize input data in an application level data structure.
The marshmallow_loader() method can be parametrized with different
schemas for the record metadata. In the provided json_v1 instance,
it uses the MetadataSchemaV1, defining the PersistentIdentifier field.
"""

from .json import json_patch_loader, marshmallow_loader
from .schemas import MetadataSchemaV1

# It uses the same schema as for the response serializers just for simplicity.
json_v1 = marshmallow_loader(MetadataSchemaV1)
json_patch_v1 = json_patch_loader

__all__ = (
    'json_v1',
    'json_patch_loader',
)
