from construct import Subconstruct, Adapter, PascalString, Bytes, Int16ub
from uuid import UUID

class Constant(object):
    HASH_SIZE = 0x20

"""
Adapters and other Construct utility classes
"""

class UUIDAdapter(Adapter):
    def __init__(self):
        """
        Construct-Adapter for UUID field.
        """
        super(self.__class__, self).__init__(Bytes(0x10))

    def _encode(self, obj, context):
            return obj.bytes

    def _decode(self, obj, context):
            return UUID(bytes_le=obj)

"""Implementation of own Enum-type"""
class EnumType(type):
    """
    Metaclass for enums.

    Creates a reverse lookup dictionary upon class initialization.
    """
    def __init__(cls, name, bases, d):
        type.__init__(cls, name, bases, d)
        cls.__reverse = dict((value, key) for key, value in d.items())

    def __contains__(cls, item):
        return item in cls.__dict__ or item in cls.__reverse

    def __getitem__(cls, item):
        if item in cls.__reverse:
            return cls.__reverse[item]
        raise AttributeError(item)


class Enum(object, metaclass=EnumType):
    """
    Helper class so that enums can just subclass `Enum`.
    """
    __metaclass__ = EnumType