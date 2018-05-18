..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

===============================
 Cookiecutter-Invenio-Datamodel
===============================

.. image:: https://img.shields.io/github/license/inveniosoftware/cookiecutter-invenio-datamodel.svg
        :target: https://github.com/inveniosoftware/cookiecutter-invenio-datamodel/blob/master/LICENSE

.. image:: https://img.shields.io/travis/inveniosoftware/cookiecutter-invenio-datamodel.svg
        :target: https://travis-ci.org/inveniosoftware/cookiecutter-invenio-datamodel

.. image:: https://img.shields.io/coveralls/inveniosoftware/cookiecutter-invenio-datamodel.svg
        :target: https://coveralls.io/r/inveniosoftware/cookiecutter-invenio-datamodel

.. image:: https://img.shields.io/pypi/v/cookiecutter-invenio-datamodel.svg
        :target: https://pypi.org/pypi/cookiecutter-invenio-datamodel

This `Cookiecutter <https://github.com/audreyr/cookiecutter>`_ template is
designed to help you to bootstrap the data model for an `Invenio
<https://github.com/inveniosoftware/invenio>`_ service.

Quickstart
----------

Install the latest Cookiecutter if you haven't installed it yet::

    pip install -U cookiecutter

Generate your Invenio datamodel::

    cookiecutter https://github.com/inveniosoftware/cookiecutter-invenio-datamodel.git

Features
--------

- **Python package:** Python package for your service.
- **Boilerplate files:** `README` including important badges, `AUTHORS` and
  `CHANGES` files.
- **License:** `MIT <https://opensource.org/licenses/MIT>`_ file and headers.
- **Installation:** Installation script written as `setup.py` and a
  requirements calculator for different levels (`min`, `pypi`).
- **Tests:** Testing setup using `pytest <http://pytest.org/latest/>`_.
- **Documentation:** Documentation generator using `Sphinx
  <http://sphinx-doc.org/>`_. Also includes all files required for `Read the
  Docs <https://readthedocs.io/>`_. Mocking module to simulate not-installed
  requirements for faster documentation building.
- **Continuous integration:** Support for `Travis <https://travis-ci.org/>`_
  which tests all requirement levels and adds coverage tests using `Coveralls
  <https://coveralls.io/>`_.
- **Your toolchain:** Ignores a decent set of files when working with Git and
  `Docker <https://www.docker.com/>`_. Gets your editor to adapt project
  guidelines by providing an `EditorConfig <http://editorconfig.org/>`_ file.

Configuration
-------------
To generate correct files, please provide the following input to Cookiecutter:

======================= =============================================
`project_name`          Full project name, might contain spaces.
`project_shortname`     Project shortname, no spaces allowed, use `-` as a
                        separator.
`package_name`          Package/Module name for Python, must follow `PEP 0008
                        <https://www.python.org/dev/peps/pep-0008/>`_.
`github_repo`           GitHub repository of the project in form of `USER/REPO`,
                        not the full GitHub URL.
`description`           A short description of the functionality of the module,
                        its length should not extend one line.
`author_name`           The name of the primary author of the project, not
                        necessarily the same as the copyright holder.
`author_email`          E-Mail address of the primary author.
`year`                  Current year.
`copyright_holder`      Name of the person or organization who acts as the
                        copyright holder of this project.
`elasticsearch_version` The version of ElasticSearch you are planning to use.
                        Versions 5.x (`v5`) and 6.x (`v6`)
                        supported at the moment.
`extension_class`       Name of the class that will be exported as
                        setuptools entrypoint and loaded by invenio
                        main app.
`config_prefix`         Prefix for the configuration keys that the
                        main app will use for this extension.
======================= =============================================

Further documentation is available on
https://cookiecutter-invenio-datamodel.readthedocs.io/
