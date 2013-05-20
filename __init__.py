from pyserializable.base import SerializableMixin, serialize, deserialize
from pyserializable.meta import SerializableMetaclass
from pyserializable.util import flatten


class Serializable(SerializableMixin, metaclass=SerializableMetaclass):
    @property
    def serial_values(self):
        return list(flatten(field.serial_values(self) for field in self._serial_fields.values()))

    def deserialize(self, values, offset=0):
        for field in self._serial_fields.values():
            offset = field.deserialize(self, values, offset)
        return offset
