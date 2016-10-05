# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""REST API for invenio-records module."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'Flask-Login>=0.3.2',
    'invenio-db[all]>=1.0.0a6',
    'invenio-indexer>=1.0.0a1',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    'citeproc': [
        'citeproc-py>=0.3.0',
        'citeproc-py-styles>=0.1.0',
    ],
    'docs': [
        'Sphinx>=1.4.2',
    ],
    'datacite': [
        'datacite>=0.2.1',
    ],
    'dublincore': [
        'dcxml>=0.1.0',
    ],
    'memento': [
        'LinkHeader>=0.4.3',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.7.0'
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'Flask-CLI>=0.2.1',
    'elasticsearch-dsl>=2.0.0',
    'invenio-pidstore>=1.0.0a9',
    'invenio-records>=1.0.0a17',
    'invenio-rest>=1.0.0a10',
    'invenio-search>=1.0.0a7',
    'invenio-query-parser>=0.6.0',
    'marshmallow>=2.5.0',
    'python-dateutil>=2.4.2',
    'six>=1.10',
    'webargs>=1.3.2',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_records_rest', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-records-rest',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio api',
    license='GPLv2',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-records-rest',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.api_apps': [
            'invenio_records_rest = invenio_records_rest:InvenioRecordsREST',
        ],
        'invenio_base.converters': [
            'pid = invenio_records_rest.utils:PIDConverter',
            'pidpath = invenio_records_rest.utils:PIDPathConverter',
        ],
        'invenio_base.api_converters': [
            'pid = invenio_records_rest.utils:PIDConverter',
            'pidpath = invenio_records_rest.utils:PIDPathConverter',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
    ],
)
