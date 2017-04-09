from io import BytesIO
from uuid import UUID
from construct import Subconstruct, StringEncoded, GreedyBytes, Bytes, Adapter

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

def _read_stream(stream, length):
    # if not isinstance(length, int):
    #     raise TypeError("expected length to be int")
    if length < 0:
        raise ValueError("length must be >= 0", length)
    data = stream.read(length)
    if len(data) != length:
        raise FieldError("could not read enough bytes, expected %d, found %d" % (length, len(data)))
    return data

class PrefixedMach2(Subconstruct):
    __slots__ = ["name", "lengthfield", "subcon"]
    def __init__(self, lengthfield, subcon):
        super(PrefixedMach2, self).__init__(subcon)
        self.lengthfield = lengthfield
    def _parse(self, stream, context, path):
        length = self.lengthfield._parse(stream, context, path)
        stream2 = BytesIO(_read_stream(stream, length * 2))
        return self.subcon._parse(stream2, context, path)
    def _build(self, obj, stream, context, path):
        stream2 = BytesIO()
        obj = self.subcon._build(obj, stream2, context, path)
        data = stream2.getvalue()
        length = len(data)
        self.lengthfield._build(length / 2, stream, context, path)
        _write_stream(stream, len(data), data)
        return obj
    def _sizeof(self, context, path):
        return self.lengthfield._sizeof(context, path) + self.subcon._sizeof(context, path)

def PascalStringMach2(lengthfield, encoding=None):
    return StringEncoded(PrefixedMach2(lengthfield, GreedyBytes), encoding)