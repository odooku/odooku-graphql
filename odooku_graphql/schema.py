import graphene
from .types import OdooObjectType


def build_schema(env):
    for model_name in env.registry.iterkeys():
        object_type = type(model_name, (OdooObjectType,), {
            'Meta': type('Meta', (object,), {
                'model': env[model_name],
                'registry': env.registry
            })
        })