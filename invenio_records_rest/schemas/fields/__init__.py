# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Custom marshmallow fields."""

from .datetime import DateString
from .generated import GenFunction, GenMethod
from .marshmallow_contrib import Function, Method
from .persistentidentifier import PersistentIdentifier
from .sanitizedhtml import SanitizedHTML
from .sanitizedunicode import SanitizedUnicode
from .trimmedstring import TrimmedString

__all__ = (
    "DateString",
    "Function",
    "GenFunction",
    "GenMethod",
    "Method",
    "PersistentIdentifier",
    "SanitizedHTML",
    "SanitizedUnicode",
    "TrimmedString",
)
