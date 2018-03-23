{% include 'misc/header.py' %}
"""{{ cookiecutter.description }}"""

from __future__ import absolute_import, print_function

from . import config


class {{ cookiecutter.extension_class }}(object):
    """{{ cookiecutter.project_name}} extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['{{ cookiecutter.project_shortname}}'] = self

    def init_config(self, app):
        """Initialize configuration.

        This Override configuration variables with the values in this package.
        """
        for k in dir(config):
            app.config[k] = getattr(config, k)
