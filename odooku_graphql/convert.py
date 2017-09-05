from odoo import fields

from singledispatch import singledispatch
from graphene import (ID, Boolean, Dynamic, Enum, Field, Float, Int, List,
                      NonNull, String, UUID)


@singledispatch
def convert_odoo_field(field, registry=None):
    return None


@convert_odoo_field.register(fields.Id)
def convert_field_to_id(field, registry):
    return ID(description=field.string, required=field.get('required', False))


@convert_odoo_field.register(fields.Char)
def convert_field_to_string(field, registry=None):
    return String(description=field.string, required=field.get('required', False))


@convert_odoo_field.register(fields.Boolean)
def convert_field_to_boolean(field, registry=None):
    return Boolean(description=field.help_text, required=field.get('required', False))