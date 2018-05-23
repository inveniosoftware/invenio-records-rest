# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Loaders."""

from .marshmallow import json_patch_loader, marshmallow_loader
from ..schemas.json import RecordSchemaJSONV1

json_v1 = marshmallow_loader(RecordSchemaJSONV1)
json_patch_v1 = json_patch_loader

__all__ = (
    'json_v1',
    'json_patch_loader',
)
