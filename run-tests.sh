#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

pydocstyle invenio_records_rest tests docs && \
isort invenio_records_rest tests --check-only --diff && \
check-manifest --ignore ".travis-*" && \
sphinx-build -qnNW docs docs/_build/html && \
py.test
