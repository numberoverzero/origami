from pyserializable.serializer import Serializer


__all__ = ['Serializer', 'autoserializer', 'serialize', 'deserialize']
_AUTO_MISSING_ATTR = "Built-in deserialization method expected value for attribute '{}' but found none."


def _autoserialized(serializer, cls):
    '''
    Decorator that automatically registers a class as serializable
        and generates a deserialize method for a class.
    The class must have a 'serial_format' attribute which is
        a format string used to serialize/deserialize attributes
        on an instance of itself.
    The class must also allow an empty constructor.  If the init
        function requires arguments, it cannot be autoserialized.
    If the attribute 'serial_attr_converters' is found, it will
        be passed to the register function as the attr_converters
        dictionary.
    If the attribute 'serial_fmt_converters' is found, it will
        be passed to the register function as the fmt_converters
        dictionary.

    See the register method for more details on how converters are used.
    '''
    attr_converters = getattr(cls, 'serial_attr_converters', None)
    fmt_converters = getattr(cls, 'serial_fmt_converters', None)
    serializer.register(
        cls, cls.serial_format,
        attr_converters=attr_converters,
        fmt_converters=fmt_converters
    )

    @classmethod
    def deserialize(cls, instance, **kwargs):
        if instance is None:
            instance = cls()
        for attr in serializer._metadata_field('cls', cls, 'attrs'):
            try:
                setattr(instance, attr, kwargs[attr])
            except KeyError:
                raise AttributeError(_AUTO_MISSING_ATTR.format(attr))
        return instance

    cls.deserialize = deserialize

    # Hook up the serializer so that we don't need to know it to serialize/deserialize objects of this type
    cls._serializer = serializer

    return cls


def autoserializer(serializer):
    '''
    Returns a class decorator that registers the class for serialization
    and adds a deserialization method to the class
    '''
    return lambda cls: _autoserialized(serializer, cls)


def serialize(obj):
    '''
    If the object's class has a _serializer field, uses that serializer.
    Otherwise, raises an AttributeError.
    '''
    cls = obj.__class__
    if hasattr(cls, '_serializer'):
        return cls._serializer.serialize(obj)
    else:
        raise AttributeError("Couldn't find a serializer for object of type '{}'".format(cls.__name__))


def deserialize(cls_or_obj, data, seek=True):
    '''
    If the class (or object's class) has a _serializer field, uses that serializer.
    Otherwise, raises an AttributeError.
    '''
    try:
        serializer = cls_or_obj._serializer
    except:
        try:
            serializer = cls_or_obj.__class__._serializer
        except:
            raise AttributeError("Couldn't find a serializer to deserialize with.")
    return serializer.deserialize(cls_or_obj, data, seek=seek)
