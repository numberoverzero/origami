import bitstring


class SerializableMixin:
    serializable_format = ''
    serializable_values = []

    def deserialize(self, values, offset=0):
        return offset


def serialize(obj):
    values = list(obj.serial_values)
    return bitstring.pack(obj.serial_format, *values)


def deserialize(obj, bitstream):
    object_array = bitstream.unpack(obj.serial_format)
    obj.deserialize(object_array)
