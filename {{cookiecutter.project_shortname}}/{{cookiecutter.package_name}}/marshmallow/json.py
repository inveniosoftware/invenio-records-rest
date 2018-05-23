{% include 'misc/header.py' %}

"""JSON Schemas."""

from invenio_records_rest.serializers.fields import DateString, \
    SanitizedUnicode
from invenio_records_rest.serializers.schemas.json import StrictKeysMixin
from marshmallow import fields, missing, validate


class PersonIdsSchemaV1(StrictKeysMixin):
    """Ids schema."""

    source = fields.Str()
    value = fields.Str()


class ContributorSchemaV1(StrictKeysMixin):
    """Contributor schema."""

    ids = fields.Nested(PersonIdsSchemaV1, many=True)
    name = fields.Str(required=True)
    role = fields.Str()
    affiliations = fields.List(fields.Str())
    email = fields.Str()


class MetadataSchemaV1(StrictKeysMixin):
    """Schema for the record metadata."""

    def get_{{ cookiecutter.pid_name }}(self, obj):
        """Get record id."""
        pid = self.context.get('pid')
        return pid.pid_value if pid else missing

    {{ cookiecutter.pid_name }} = fields.Method(deserialize='get_{{ cookiecutter.pid_name }}')
    title = SanitizedUnicode(required=True, validate=validate.Length(min=3))
    keywords = fields.Nested(fields.Str(), many=True)
    publication_date = DateString()
    contributors = fields.Nested(ContributorSchemaV1, many=True, required=True)


class RecordSchemaV1(StrictKeysMixin):
    """Record schema."""

    metadata = fields.Nested(MetadataSchemaV1)
    created = fields.Str(dump_only=True)
    revision = fields.Integer(dump_only=True)
    updated = fields.Str(dump_only=True)
    id = fields.Number(
        required=True, attribute='metadata.{{ cookiecutter.pid_name }}')
