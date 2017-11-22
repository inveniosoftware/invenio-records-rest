..
    This file is part of Invenio.
    Copyright (C) 2015 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


API Docs
========

.. automodule:: invenio_records_rest.ext
   :members:

Facets
------

.. automodule:: invenio_records_rest.facets
   :members:

Sorter
------

.. automodule:: invenio_records_rest.sorter
   :members:

Links
-----

.. automodule:: invenio_records_rest.links
   :members:

Query
-----

.. automodule:: invenio_records_rest.query
   :members:

Utils
-----

.. automodule:: invenio_records_rest.utils
   :members:

Errors
------

.. automodule:: invenio_records_rest.errors
   :members:

Views
-----

.. automodule:: invenio_records_rest.views
   :members:
   :exclude-members: need_record_permission verify_record_permission

Permissions
-----------

Permissions are handled by the following decorator, which is used in the
record's REST resources:

.. autofunction:: invenio_records_rest.views.need_record_permission

each resource method is checking the permissions through this decorator, with
``read_permission_factory``, ``create_permission_factory``,
``update_permission_factory`` and ``delete_permission_factory`` as argument,
where the implementation of each can be configured for each REST
endpoint with :data:`invenio_records_rest.config.RECORDS_REST_ENDPOINTS`
(using ``{read,create,update,delete}_permission_factory_imp`` keys).

For reference on each resource method and the default permission factory,
refer to the methods' docstrings in the Views section above.

