# SPDX-FileCopyrightText: 2018 CERN.
# SPDX-FileCopyrightText: 2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Persistent Identifier field."""

from marshmallow import missing
from marshmallow_utils.context import context_schema

from invenio_records_rest.schemas.fields.generated import GenFunction


def pid_from_context(*args, **kwargs):
    """Get PID from marshmallow context."""
    pid = context_schema.get().get("pid", False)
    return pid.pid_value if pid else missing


class PersistentIdentifier(GenFunction):
    """Field to handle PersistentIdentifiers in records.

    .. versionadded:: 1.2.0
    """

    def __init__(self, *args, **kwargs):
        """Initialize field."""
        super().__init__(
            serialize=pid_from_context, deserialize=pid_from_context, *args, **kwargs
        )
