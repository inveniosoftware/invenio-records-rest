"""JSON loaders."""

from flask import request

from .errors import MarshmallowErrors


def marshmallow_loader(schema_class):
    """Marshmallow loader for JSON requests.
    simplicity, but it can
    """
    def json_loader():
        request_json = request.get_json()

        context = {}
        pid_data = request.view_args.get('pid_value')
        if pid_data:
            pid, _ = pid_data.data
            context['pid'] = pid

        result = schema_class(context=context).load(request_json)

        if result.errors:
            raise MarshmallowErrors(result.errors)
        return result.data
    return json_loader


def json_patch_loader():
    """Dummy loader for json-patch requests."""
    return request.get_json(force=True)
