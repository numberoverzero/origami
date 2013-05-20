import collections
from pyserializable.util import noop
from pyserializable.field import Field


class SerializableMetaclass(type):
    @classmethod
    def __prepare__(cls, name, bases):
        return collections.OrderedDict()

    def __new__(cls, name, bases, attrs):
        serial_fields = collections.OrderedDict()
        for attr_name, attr_val in attrs.items():
            if isinstance(attr_val, Field):
                serial_fields[attr_name] = attr_val
                attr_val.name = attr_name
        attrs['_serial_fields'] = serial_fields

        real_init = attrs.get('__init__', noop)

        def fake_init(self, *args, **kwargs):
            for field_name, field in self._serial_fields.items():
                setattr(self, field_name, field.instance)
            real_init(self, *args, **kwargs)
        attrs['__init__'] = fake_init

        if '__str__' not in attrs:
            def str_(self):
                cls_name = self.__class__.__name__
                fmt = '{}={}'
                decl_iter = (fmt.format(fname, str(getattr(self, fname))) for fname in self._serial_fields)
                decl_str = ', '.join(decl_iter)
                return '{}({})'.format(cls_name, decl_str)
            attrs['__str__'] = str_

        print("Generating serial_format for class {}".format(name))
        fmt_iter = (f.serial_format for f in serial_fields.values())
        serial_format = ', '.join(fmt_iter)
        attrs['serial_format'] = serial_format

        return super().__new__(cls, name, bases, attrs)
