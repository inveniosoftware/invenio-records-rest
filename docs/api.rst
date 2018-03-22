..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

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

