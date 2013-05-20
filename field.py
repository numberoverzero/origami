from pyserializable.util import passthrough
from pyserializable.base import SerializableMixin


class Field(SerializableMixin):
    def __get__(self, obj, *args):
        return self.raw_get(obj)

    def __set__(self, obj, value):
        self.raw_set(obj, value)

    def raw_get(self, obj):
        '''Direct manipulation of raw value'''
        try:
            return obj.__dict__[self.name]
        except (AttributeError, KeyError):
            return self.instance

    def raw_set(self, obj, value):
        '''Direct manipulation of raw value'''
        obj.__dict__[self.name] = value

    def serial_values(self, obj):
        raise NotImplementedError("Abstract field method")

    def deserialize(self, obj, values, offset=0):
        raise NotImplementedError("Abstract field method")

    @property
    def instance(self):
        raise NotImplementedError("Abstract field method")


class DeferredClassWrapperField(Field):
    def __init__(self, cls, *args, **kwargs):
        assert issubclass(cls, SerializableMixin)
        self.cls = cls
        self.serial_format = cls.serial_format
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def serial_values(self, obj):
        return self.raw_get(obj).serial_values

    def deserialize(self, obj, values, offset=0):
        return self.raw_get(obj).deserialize(values, offset)

    @property
    def instance(self):
        return self.cls(*(self.args), **(self.kwargs))


class ExplicitSerialField(Field):
    def __init__(self, format='', default=None, to_serial=passthrough, from_serial=passthrough):
        self.serial_format = format
        self.default = default
        self.to_serial = to_serial
        self.from_serial = from_serial

    def serial_values(self, obj):
        raw_object = self.__get__(obj)
        serial_object = self.to_serial(raw_object)
        return serial_object

    def deserialize(self, obj, values, offset=0):
        serial_object = values[offset]
        raw_object = self.from_serial(serial_object)
        self.__set__(obj, raw_object)
        return offset + 1

    @property
    def instance(self):
        return self.default


def field(*args, **kwargs):
    #Serial class takes one arg, explicit fields take no args
    assert len(args) < 2

    # Wrapping a serializable class
    if len(args) == 1 and not kwargs:
        cls = args[0]
        return DeferredClassWrapperField(cls)
    #Creating a scalar field
    else:
        return ExplicitSerialField(**kwargs)
