from functools import wraps
import collections
import bitstring


noop_init = lambda *a, **kw: None
passthrough = lambda v: v


def flatten(l, ltypes=collections.Sequence):
    l = list(l)
    while l:
        if isinstance(l[0], str):
            yield l.pop(0)
            continue
        while l and isinstance(l[0], ltypes):
            l[0:1] = l[0]
        if l:
            yield l.pop(0)


def serialize(obj):
    values = list(obj.serial_values)
    return bitstring.pack(obj.serial_format, *values)


def deserialize(obj, bitstream):
    object_array = bitstream.unpack(obj.serial_format)
    obj.deserialize(object_array)


class SerializableMixin(object):
    serializable_format = ''
    serializable_values = []

    def deserialize(self, values, offset=0):
        return offset


class Field(object):
    def __init__(self, cls, *args, **kwargs):
        '''
        Allows us to defer instantation of an attribute
        of a class from class creation
        '''
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def __get__(self, obj, *args):
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        obj.__dict__[self.name] = value

    @property
    def instance(self):
        return self.cls(*(self.args), **(self.kwargs))


class ClassWrapperField(Field, SerializableMixin):
    def __init__(self, cls, *args, **kwargs):
        assert issubclass(cls, SerializableMixin)
        super().__init__(cls, *args, **kwargs)
        self.serial_format = self.cls.serial_format

    def serial_values(self, obj):
        return self.__get__(obj).serial_values

    def deserialize(self, obj, values, offset=0):
        return self.__get__(obj).deserialize(values, offset)


class RawSerialField(Field, SerializableMixin):
    def __init__(self, format='', default=None,
                 to_serial=passthrough, from_serial=passthrough):
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


def f(*args, **kwargs):
    '''
    Wraps a SerializableMixin class so it can Fieldatized,
    or constructs a RawSerialField if kwargs are passed
    '''
    assert len(args) < 2  # If it's a SerializableMixin class,
                          # it should be exactly one arg
                          # and no kwargs.  If it's a RawSerialField,
                          # everything should be kwargs.

    if len(args) == 1 and not kwargs:
        cls = args[0]

        @wraps(cls)
        def init(*args, **kwargs):
            return ClassWrapperField(cls, *args, **kwargs)
        return init
    return RawSerialField(**kwargs)


class DeclarativeMetaclass(type):
    @classmethod
    def __prepare__(cls, name, bases):
        return collections.OrderedDict()

    def __new__(cls, name, bases, attrs):
        declared_fields = collections.OrderedDict()
        for attr_name, attr_val in attrs.items():
            if isinstance(attr_val, Field):
                declared_fields[attr_name] = attr_val
                attr_val.name = attr_name
        attrs['_declared_fields'] = declared_fields

        serial_fields = collections.OrderedDict()
        for attr_name, attr_val in declared_fields.items():
            if isinstance(attr_val, SerializableMixin):
                serial_fields[attr_name] = attr_val
        attrs['_serial_fields'] = serial_fields

        fmt_gen = (f.serial_format for f in serial_fields.values())
        serial_format = ', '.join(fmt_gen)
        attrs['serial_format'] = serial_format

        real_init = attrs.get('__init__', noop_init)

        def fake_init(self, *args, **kwargs):
            for field_name, field in self._declared_fields.items():
                setattr(self, field_name, field.instance)
            real_init(self, *args, **kwargs)
        attrs['__init__'] = fake_init

        if '__str__' not in attrs:
            def str_(self):
                cls_name = self.__class__.__name__
                fmt = lambda item: '{}={}'.format(
                    item[0], str(item[1].__get__(self)))
                decl_iter = ', '.join(map(fmt, self._declared_fields.items()))
                return '{}({})'.format(cls_name, decl_iter)
            attrs['__str__'] = str_

        return super().__new__(cls, name, bases, attrs)


class Serializable(SerializableMixin, metaclass=DeclarativeMetaclass):
    @property
    def serial_values(self):
        values = lambda field: field.serial_values(self)
        values_gen = map(values, self._serial_fields.values())
        return list(flatten(values_gen))

    def deserialize(self, values, offset=0):
        for field in self._serial_fields.values():
            offset = field.deserialize(self, values, offset)
        return offset
