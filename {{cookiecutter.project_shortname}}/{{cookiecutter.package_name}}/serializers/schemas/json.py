from marshmallow import Schema, ValidationError, fields, validate, \
    validates_schema

from ..fields import DateString, SanitizedHTML


class StrictKeysMixin(Schema):
    """Ensure only valid keys exists."""

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        """Check for unknown keys."""
        if isinstance(original_data, list):
            for elem in original_data:
                self.check_unknown_fields(data, elem)
        else:
            for key in original_data:
                if key not in [
                        self.fields[field].attribute or field
                        for field in self.fields
                ]:
                    raise ValidationError(
                        'Unknown field name {}'.format(key), field_names=[key])


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
    """Schema for a record."""

    title = SanitizedHTML(required=True, validate=validate.Length(min=3))
    keywords = fields.Nested(fields.Str(), many=True)
    publication_date = DateString()
    contributors = fields.Nested(ContributorSchemaV1, many=True, required=True)


class RecordSchemaV1(StrictKeysMixin):
    """Schema for records v1 in JSON."""

    metadata = fields.Nested(MetadataSchemaV1)
    {{ cookiecutter.pid_name }} = fields.Number(
        required=True, attribute='metadata.{{ cookiecutter.pid_name }}')
    created = fields.Str(dump_only=True)
    revision = fields.Integer(dump_only=True)
    updated = fields.Str(dump_only=True)
