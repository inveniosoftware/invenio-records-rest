# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Records REST errors.

All error classes in this module are inheriting from
:class:`invenio_rest.errors.RESTException` or
:class:`invenio_rest.errors.RESTValidationError`.
"""

from flask import request
from invenio_i18n import gettext as _
from invenio_rest.errors import FieldError, RESTException, RESTValidationError


#
# Search
#
class SearchPaginationRESTError(RESTException):
    """Search pagination error."""

    code = 400

    def __init__(self, errors=None, **kwargs):
        """Initialize exception."""
        _errors = []
        if errors:
            for field, messages in errors.items():
                _errors.extend([FieldError(field, msg) for msg in messages])
        super().__init__(errors=_errors, **kwargs)


#
# Query
#
class InvalidQueryRESTError(RESTException):
    """Invalid query syntax."""

    code = 400

    # We can't use lazy_gettext for the description field because it doesn't serialize correctly to JSON.
    # To ensure the translated description is included in JSON output, we translate it in the constructor.
    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("Invalid query syntax.")
        super().__init__(**kwargs)


#
# CiteProc
#
class StyleNotFoundRESTError(RESTException):
    """No such style."""

    code = 400

    def __init__(self, style=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "Style %(style)s could not be found.",
                style=f'"{style}"' if style else "",
            )
        super().__init__(**kwargs)


#
# PID
#
class PIDRESTException(RESTException):
    """Base REST API PID exception class."""

    def __init__(self, pid_error=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        self.pid_error = pid_error


class PIDDoesNotExistRESTError(PIDRESTException):
    """Non-existent PID."""

    code = 404

    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("PID does not exist.")
        super().__init__(**kwargs)


class PIDUnregisteredRESTError(PIDRESTException):
    """Unregistered PID."""

    code = 404

    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("PID is not registered.")
        super().__init__(**kwargs)


class PIDDeletedRESTError(PIDRESTException):
    """Deleted PID."""

    code = 410

    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("PID has been deleted.")
        super().__init__(**kwargs)


class PIDMissingObjectRESTError(PIDRESTException):
    """PID missing object."""

    code = 500

    def __init__(self, pid, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("No object assigned to %(pid)s.", pid=pid)
        super().__init__(**kwargs)


class PIDRedirectedRESTError(PIDRESTException):
    """Invalid redirect for destination."""

    code = 500

    def __init__(self, pid_type=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "Invalid redirect - pid_type %(pid_type)s endpoint missing.",
                pid_type=f'"{pid_type}"' if pid_type else "",
            )
        super().__init__(**kwargs)


#
# Views
#
class PIDResolveRESTError(RESTException):
    """Invalid PID."""

    code = 500

    def __init__(self, pid=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "PID %(pid)s could not be resolved.", pid=f"#{pid}" if pid else ""
            )
        super().__init__(**kwargs)


class UnsupportedMediaRESTError(RESTException):
    """Creating record with unsupported media type."""

    code = 415

    def __init__(self, content_type=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                'Unsupported media type "%(content_type)s".',
                content_type=content_type or request.mimetype,
            )
        super().__init__(**kwargs)


class InvalidDataRESTError(RESTException):
    """Invalid request body."""

    code = 400

    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("Could not load data.")
        super().__init__(**kwargs)


class PatchJSONFailureRESTError(RESTException):
    """Failed to patch JSON."""

    code = 400

    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _("Could not patch JSON.")
        super().__init__(**kwargs)


class SuggestMissingContextRESTError(RESTException):
    """Missing a context value when getting record suggestions."""

    code = 400

    def __init__(self, ctx_field=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "Missing %(ctx_field)s context.",
                ctx_field=f'"{ctx_field}"' if ctx_field else "",
            )
        super().__init__(**kwargs)


class SuggestNoCompletionsRESTError(RESTException):
    """No completion requested when getting record suggestions."""

    code = 400

    def __init__(self, options=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "No completions requested.%(options)s",
                options=f" (options: {options})" if options else "",
            )
        super().__init__(**kwargs)


class JSONSchemaValidationError(RESTValidationError):
    """JSONSchema validation error exception."""

    code = 400

    def __init__(self, error=None, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "Validation error: %(error)s.", error=error.message if error else ""
            )
        super().__init__(**kwargs)


class UnhandledSearchError(RESTException):
    """Failed to handle exception."""

    code = 500

    def __init__(self, **kwargs):
        """Initialize exception."""
        if "description" not in kwargs:
            kwargs["description"] = _(
                "An internal server error occurred when handling the request."
            )
        super().__init__(**kwargs)
