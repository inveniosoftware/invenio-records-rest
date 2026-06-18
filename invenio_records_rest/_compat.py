# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""Python 2/3 compatibility helpers."""

try:  # Python 3 way of inspecting functions
    from inspect import Parameter, signature

    def wrap_links_factory(links_factory):
        """Test if the links_factory function accepts kwargs."""
        sign = signature(links_factory)
        kwargs_param = [
            p for p in sign.parameters.values() if p.kind == Parameter.VAR_KEYWORD
        ]
        return len(kwargs_param) == 0

except ImportError:  # Python 2 way of inspecting functions
    from inspect import getargspec

    def wrap_links_factory(links_factory):
        """Test if the links_factory function accepts kwargs."""
        spec = getargspec(links_factory)
        return spec.keywords is None
