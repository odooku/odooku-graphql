from collections import OrderedDict

from graphene import Field
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs

from .convert import convert_odoo_field


def construct_fields(model, registry, only_fields, exclude_fields):
    fields = OrderedDict()
    for field_name, odoo_field in model.sudo().fields_get().iteritems():
        is_not_in_only = only_fields and field_name not in only_fields
        is_excluded = field_name in exclude_fields
        if is_not_in_only or is_excluded:
            continue

        field = convert_odoo_field(odoo_field, registry)
        if field is not None:
            fields[field_name] = field

    return fields


class OdooObjectTypeOptions(ObjectTypeOptions):
    model = None


class OdooObjectType(ObjectType):

    @classmethod
    def __init_subclass_with_meta__(cls, model=None, registry=None,
                                    only_fields=(), exclude_fields=(),
                                    interfaces=(), **options):

        odoo_fields = yank_fields_from_attrs(
            construct_fields(model, registry, only_fields, exclude_fields),
            _as=Field,
        )

        _meta = OdooObjectTypeOptions(cls)
        _meta.model = model
        _meta.registry = registry
        _meta.fields = odoo_fields

        super(OdooObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta,
            interfaces=interfaces,
            **options
        )

        registry[model._name]._schema = cls
