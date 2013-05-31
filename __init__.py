from pyserializable.serializer import Serializer, get_serializer
import uuid

__all__ = ['Serializer', 'serialized', 'serialize', 'deserialize', 'get_serializer']

_AUTO_MISSING_ATTR = "Built-in deserialization method expected value for attribute '{}' but found none."
_global_serializer_name = str(uuid.uuid4())
_global_serializer = Serializer(_global_serializer_name)


def serialize(obj):
    cls = obj.__class__
    if hasattr(cls, 'serial_metadata'):
        return cls.serial_metadata['serializer'].serialize(obj)
    else:
        raise AttributeError("Couldn't find a serializer for object of type '{}'".format(cls.__name__))


def deserialize(cls_or_obj, data):
    try:
        serializer = cls_or_obj.serial_metadata['serializer']
    except:
        try:
            serializer = cls_or_obj.__class__.serial_metadata['serializer']
        except:
            raise AttributeError("Couldn't find a serializer to deserialize with.")
    return serializer.deserialize(cls_or_obj, data)


def serialized(arg):
    # If arg passed to decorator is a string, return a decorator for that specific serializer
    if isinstance(arg, str):
        def class_decorator(cls):
            return _wrap_class(arg, cls)
        return class_decorator
    # If arg passed isn't a string, it's a class - use the global serializer for this class
    else:
        return _wrap_class(_global_serializer_name, arg)


def _wrap_class(registered_name, cls):
    serializer = get_serializer(registered_name)
    attr_converters = getattr(cls, 'serial_attr_converters', None)
    fmt_converters = getattr(cls, 'serial_fmt_converters', None)
    serializer.register(
        cls, cls.serial_format,
        attr_converters=attr_converters,
        fmt_converters=fmt_converters
    )

    if hasattr(cls, 'deserialize'):
        return cls

    @classmethod
    def deserialize(cls, instance, **kwargs):
        if instance is None:
            instance = cls()
        for attr, fmt in cls.serial_metadata['serial_format']:
            try:
                setattr(instance, attr, kwargs[attr])
            except KeyError:
                raise AttributeError(_AUTO_MISSING_ATTR.format(attr))
        return instance

    cls.deserialize = deserialize

    return cls
