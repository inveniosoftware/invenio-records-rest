{% include 'misc/header.py' %}
"""{{ cookiecutter.description }}"""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.3.3',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

invenio_search_version = '1.0.0'
invenio_db_version = '1.0.0'

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    # Elasticsearch version
    'elasticsearch5': [
        'invenio-search[elasticsearch5]>={}'.format(invenio_search_version),
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]>={}'.format(invenio_search_version),
    ],
    # Databases
    'mysql': [
        'invenio-db[mysql]>={}'.format(invenio_db_version),
    ],
    'postgresql': [
        'invenio-db[postgresql]>={}'.format(invenio_db_version),
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name[0] == ':' or name in ('elasticsearch5', 'elasticsearch6', 'mysql',
                                  'postgresql'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    # TODO: use the pypi version of invenio-records-rest once it's released
    # 'invenio-records-rest>=1.0.2,<1.1.0',
    'arrow>=0.12.1',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('{{ cookiecutter.package_name }}', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='{{ cookiecutter.project_shortname }}',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='{{ cookiecutter.project_shortname }} Invenio TODO',
    license='MIT',
    author='{{ cookiecutter.author_name }}',
    author_email='{{ cookiecutter.author_email }}',
    url='https://github.com/{{ cookiecutter.github_repo }}',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            '{{ cookiecutter.package_name }} = {{ cookiecutter.package_name }}:{{ cookiecutter.extension_class }}',
        ],
        'invenio_base.api_apps': [
            '{{ cookiecutter.package_name }} = {{ cookiecutter.package_name }}:{{ cookiecutter.extension_class }}',
        ],
        'invenio_jsonschemas.schemas': [
            '{{ cookiecutter.package_name}} = {{ cookiecutter.package_name}}.jsonschemas'
        ],
        'invenio_search.mappings': [
            'records = {{ cookiecutter.package_name}}.mappings'
        ]
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Planning',
    ],
)
