# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API for Records."""

from __future__ import absolute_import, print_function

from .ext import InvenioRecordsREST
from .proxies import current_records_rest
from .version import __version__

__all__ = ('__version__', 'current_records_rest', 'InvenioRecordsREST')
