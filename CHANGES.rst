..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.1.2 (released 2018-06-26)

- Rename authentication of GET operation over
  RecordsListResource from 'read_list' to 'list'.

Version 1.1.1 (released 2018-06-25)

- Adds authentication to GET operation over
  RecordsListResource.
- Bumps invenio-db version (min v1.0.2).

Version 1.1.0 (released 2018-05-26)

- Moves RecordSchemaJSONV1 marshmallow schema from
  invenio_records_rest.serializers.schemas to
  invenio_records_rest.schemas.
- Fixes missing API documentation.
- Adds blueprint factory (requires Invenio-Base v1.0.1+).
- Adds marshmallow loaders, fields and schemas.

Version 1.0.1 (released 2018-03-27)

- Fixes unicode query handling
- Fixes Datacite v4.1 serialization

Version 1.0.0 (released 2018-03-23)

- Initial public release.
