from graphene.types.objecttype import ObjectType, ObjectTypeOptions


class OdooObjectTypeOptions(ObjectTypeOptions):
    model = None
    registry = None


class OdooObjectType(ObjectType):
    pass