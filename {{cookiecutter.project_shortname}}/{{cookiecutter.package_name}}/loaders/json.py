"""JSON loaders."""

from flask import request

from .errors import MarshmallowErrors


def marshmallow_loader(schema_class):
    """Marshmallow loader for JSON requests.
    simplicity, but it can
    """
    def json_loader():
        request_json = request.get_json()

        result = schema_class().load(request_json)

        if result.errors:
            raise MarshmallowErrors(result.errors)
        return result.data
    return json_loader


def json_patch_loader():
    """Dummy loader for json-patch requests."""
    return request.get_json(force=True)
