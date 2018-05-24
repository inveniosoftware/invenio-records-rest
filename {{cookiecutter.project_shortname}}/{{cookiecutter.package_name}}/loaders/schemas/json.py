"""JSON schemas for the loaders."""


from marshmallow import fields, missing

from ...serializers.schemas import MetadataSchemaV1 as BaseMetadataSchemaV1


class MetadataSchemaV1(BaseMetadataSchemaV1):
    """Metadata schema."""

    {{ cookiecutter.pid_name }} = fields.Method(deserialize='get_{{ cookiecutter.pid_name }}')

    def get_{{ cookiecutter.pid_name }}(self, obj):
        """Get record id."""
        pid = self.context.get('pid')
        return pid.pid_value if pid else missing
