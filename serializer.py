from pyserializable.util import multidelim_generator
import bitstring

_MISSING_ATTR = "'{}' object was missing expected attribute '{}'"
_DUPLICATE_SERIALIZER = "Cannot register Serializer with name '{}': already registered"
_serializers = {}


class Serializer(object):
    def __init__(self, registered_name):
        self.registered_classes = []
        self.class_map = {}
        if registered_name in _serializers:
            raise KeyError(_DUPLICATE_SERIALIZER.format(registered_name))
        _serializers[registered_name] = self

    def register(self, cls, format, attr_converters=None, fmt_converters=None):
        serial_format, flat = [], []
        for name, fmt in multidelim_generator(format, ',', '='):
            if fmt in self.class_map:
                subcls = self.class_map[fmt]
                flat.append(subcls.serial_metadata['bitstring_format'])
                serial_format.append((name, subcls))
            else:
                flat.append(fmt)
                serial_format.append((name, fmt))
        bitstring_format = ','.join(flat)
        flat_count = len(bitstring_format.split(','))

        metadata = {
            'attr_converters': attr_converters or {},
            'bitstring_format': bitstring_format,
            'flat_count': flat_count,
            'fmt_converters': fmt_converters or {},
            'serializer': self,
            'serial_format': serial_format,

        }

        cls.serial_metadata = metadata
        self.registered_classes.append(cls)
        self.class_map[cls.__name__] = cls

    def serialize(self, obj):
        values = self._get_flat_values(obj)
        fmt = obj.__class__.serial_metadata['bitstring_format']
        return bitstring.pack(fmt, *values)

    def deserialize(self, cls_or_obj, data, seek=True):
        cls, instance = self._get_cls_obj(cls_or_obj)
        fmt = cls.serial_metadata['bitstring_format']
        values = data.unpack(fmt)
        return self._obj_from_values(cls, instance, values, pos=0)

    def _get_flat_values(self, obj):
        values = []

        meta = obj.__class__.serial_metadata
        attr_converters = meta['attr_converters']
        fmt_converters = meta['fmt_converters']

        for attr, fmt in meta['serial_format']:
            try:
                data = getattr(obj, attr)
            except AttributeError:
                raise AttributeError(_MISSING_ATTR.format(obj.__class__.__name__, attr))

            if fmt in self.registered_classes:
                values.extend(self._get_flat_values(data))
            else:
                if attr in attr_converters:
                    data = attr_converters[attr][0](data)
                elif fmt in fmt_converters:
                    data = fmt_converters[fmt][0](data)
                values.append(data)
        return values

    def _obj_from_values(self, cls, instance, values, pos=0):
        kwargs = {}

        meta = cls.serial_metadata
        format = meta['serial_format']
        attr_converters = meta['attr_converters']
        fmt_converters = meta['fmt_converters']

        for attr, fmt in format:
            if isinstance(fmt, str):
                value = values[pos]
                if attr in attr_converters:
                    value = attr_converters[attr][1](value)
                elif fmt in fmt_converters:
                    value = fmt_converters[fmt][1](value)
                offset = 1
            elif fmt in self.registered_classes:
                value = self._obj_from_values(fmt, None, values, pos=pos)
                offset = fmt.serial_metadata['flat_count']
            kwargs[attr] = value
            pos += offset
        return cls.deserialize(instance, **kwargs)

    def _get_cls_obj(self, cls_or_obj):
        instance = None

        #Class object
        if cls_or_obj in self.registered_classes:
            cls = cls_or_obj
        #Class string
        elif cls_or_obj in self.class_map:
            cls = self.class_map[cls_or_obj]
        #Instance
        elif cls_or_obj.__class__ in self.registered_classes:
            cls = cls_or_obj.__class__
            instance = cls_or_obj
        else:
            raise ValueError("Don't know how to deserialize {}".format(cls_or_obj))
        return cls, instance


def get_serializer(registered_name):
    return _serializers[registered_name]
