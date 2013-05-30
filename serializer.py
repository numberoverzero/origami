from pyserializable.util import multidelim_generator
import bitstring

_MISSING_ATTR = "'{}' object was missing expected attribute '{}'"


class Serializer(object):
    def __init__(self):
        self._cls = {}
        self._cls_metadata = {}

    def register(self, cls, format, attr_converters=None, fmt_converters=None):
        '''
        cls: The class to register.  This should have a classmethod called
            'deserialize' which has the signature:
                deserialize(cls, instance, **kwargs).
            instance may be an instance of the class, or None if
            only the class was provided.  For each key => value pair,
            the key is an attribute of the instance whose deserialized value
            is value.  In other words, <inst of cls>.key = value
        format: Format string of comma-separated name=format pairs,
            where each name is a string of an attribute on instances
            of cls that can be serialized and deserialized.
            Example: 'r=uint:8, g=uint:8, b=uint:8' would serialize
            the r, g, b attributes on an instance of cls.
        attr_converters: dictionary of name => [func, func] where name
            is a string of an attribute on instances of cls.
            Each function should take one value and return one value.
            The first function should return a value which can be serialized
            according to the format specified in the format string above.
            The second function takes a value which is returned from unpacking
            a bitstring.  The value returned by this function will be inserted
            for the attribute named into an instance of the cls.
        fmt_converters: dictionary of format => func, func much like
            attr_converters, except each key is a string representing a format
            field that may be in the format string above.  The functions are
            identical to those in attr_converters.  For each format key in this
            dictionary, any attribute with the same format string will use these
            converters when serializing/deserializing.

        If an attribute is mapped in attr_converters and its format is
            mapped in fmt_converters, then its attribute converter
            will be used instead of its format converter.
        '''
        metadata = self._generate_metadata(
            cls, format,
            attr_converters=attr_converters,
            fmt_converters=fmt_converters
        )
        self._cls[cls.__name__] = cls
        self._cls_metadata[cls] = metadata

    def serialize(self, obj):
        values = self._get_flat_values(obj)
        fmt = self._cls_metadata[obj.__class__]['bitstring_format']
        return bitstring.pack(fmt, *values)

    def deserialize(self, cls_or_obj, data, seek=True):
        '''
        Takes a registered class or an instance of a registered class
        and a bitstring.BitStream object and returns an instance of
        the class with the data in the BitStream deserialized into
        the new instance according to the format registered for the class.
        '''
        instance = None

        #Class object
        if cls_or_obj in self._cls_metadata:
            cls = cls_or_obj
        #Class string
        elif cls_or_obj in self._cls:
            cls = cls_from_str(cls_or_obj)
        #Instance
        elif cls_or_obj.__class__ in self._cls_metadata:
            cls = cls_or_obj.__class__
            instance = cls_or_obj
        else:
            raise ValueError("Don't know how to deserialize {}".format(cls_or_obj))

        kwargs = {}
        if seek:
            data.pos = 0

        attr_converters = self._cls_metadata[cls]['attr_converters']
        fmt_converters = self._cls_metadata[cls]['fmt_converters']

        for attr, fmt in self._cls_metadata[cls]['serial_format']:
            if fmt in self._cls_metadata:
                kwargs[attr] = self.deserialize(fmt, data, seek=False)
            else:
                value = data.read(fmt)
                # Check for converters for this object.
                # Attribute converters take precedence.
                if attr in attr_converters:
                    value = attr_converters[attr][1](value)
                elif fmt in fmt_converters:
                    value = fmt_converters[fmt][1](value)
                kwargs[attr] = value
        return cls.deserialize(instance, **kwargs)

    def _get_flat_values(self, obj):
        values = []

        cls = obj.__class__
        attr_converters = self._cls_metadata[cls]['attr_converters']
        fmt_converters = self._cls_metadata[cls]['fmt_converters']

        for attr, fmt in self._cls_metadata[cls]['serial_format']:
            try:
                data = getattr(obj, attr)
            except AttributeError:
                raise AttributeError(_MISSING_ATTR.format(cls.__name__, attr))

            if fmt in self._cls_metadata:
                # Serializable object, get its attributes
                sub_values = self._get_flat_values(data)
                values.extend(sub_values)
            else:
                # Attribute converters take precedence.
                if attr in attr_converters:
                    data = attr_converters[attr][0](data)
                elif fmt in fmt_converters:
                    data = fmt_converters[fmt][0](data)
                values.append(data)

        return values

    def _generate_metadata(self, cls, format, attr_converters=None, fmt_converters=None):
            serial_format, flat = [], []
            for name, fmt in multidelim_generator(format, ',', '='):
                if fmt in self._cls:
                    subcls = self._cls[fmt]
                    flat.append(self._cls_metadata[subcls]['bitstring_format'])
                    serial_format.append((name, subcls))
                else:
                    flat.append(fmt)
                    serial_format.append((name, fmt))

            metadata = {
                'cls': cls,
                'cls_str': cls.__name__,
                'serial_format': serial_format,
                'bitstring_format': ','.join(flat),
                'attr_converters': attr_converters or {},
                'fmt_converters': fmt_converters or {}
            }

            return metadata
