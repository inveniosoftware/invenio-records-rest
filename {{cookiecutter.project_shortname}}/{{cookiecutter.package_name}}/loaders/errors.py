"""Error class for JSON loaders."""

import json

from invenio_rest.errors import RESTValidationError


def _flatten_marshmallow_errors(self, errors):
    """Flatten marshmallow errors."""
    res = []
    for field, error in errors.items():
        if isinstance(error, list):
            res.append(
                dict(field=field, message=' '.join([str(x) for x in error])))
        elif isinstance(error, dict):
            res.extend(_flatten_marshmallow_errors(error))
    return res


class MarshmallowErrors(RESTValidationError):
    """Marshmallow validation errors."""

    def __init__(self, errors):
        """Store marshmallow errors."""
        self._it = None
        self.errors = _flatten_marshmallow_errors(errors)
        super(MarshmallowErrors, self).__init__()

    def __str__(self):
        """Print exception with errors."""
        return "{base}. Encountered errors: {errors}".format(
            base=super(RESTValidationError, self).__str__(),
            errors=self.errors)

    def __iter__(self):
        """Get iterator."""
        self._it = iter(self.errors)
        return self

    def next(self):
        """Python 2.7 compatibility."""
        return self.__next__()  # pragma: no cover

    def __next__(self):
        """Get next file item."""
        return next(self._it)

    def get_body(self, environ=None):
        """Get the request body."""
        body = dict(
            status=self.code,
            message=self.get_description(environ),
        )

        if self.errors:
            body['errors'] = self.errors

        return json.dumps(body)
