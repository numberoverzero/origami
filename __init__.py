import collections
import bitstring


PREFIX = "Serial_"
indexes = {}
attributes = ['cls', 'cls_str', 'normalized_cls_str', 'raw_format', 'compact_format']

#  Build indexes into metadata so we can get at it by most properties
for attr in attributes:
    indexes[attr] = {}


def register(cls, format, attr_converters=None, fmt_converters=None):
    metadata = generate_metadata(
        cls, format,
        attr_converters=attr_converters,
        fmt_converters=fmt_converters
    )
    for attr, index in indexes.items():
        index[metadata[attr]] = metadata


def normalized_class_str(cls_or_str):
    '''Centralized normalizing logic so we don't have PREFIX sprinkled throughout our functions'''
    if not isinstance(cls_or_str, str):
        cls_or_str = cls_or_str.__name__
    return PREFIX + cls_or_str


def generate_metadata(cls, raw_format, attr_converters=None, fmt_converters=None):
        metadata = {}
        metadata['cls'] = cls
        metadata['cls_str'] = cls.__name__
        metadata['normalized_cls_str'] = normalized_class_str(cls)
        metadata['raw_format'] = raw_format

        pieces = raw_format.split(',')
        compact_pieces = []
        for piece in pieces:
            name, format = [p.strip() for p in piece.split('=')]
            if has_registered_class(format, normalized=False):
                compact_pieces.append('{}={}'.format(normalized_class_str(format), name))
            else:
                compact_pieces.append('{}={}'.format(format, name))
        compact_format = ','.join(compact_pieces)
        metadata['compact_format'] = compact_format

        formats = raw_format.split(',')
        attrs = [fmt.split('=')[0].strip() for fmt in formats]
        metadata['attrs'] = attrs

        metadata['attr_converters'] = attr_converters or {}
        metadata['fmt_converters'] = fmt_converters or {}

        return metadata


def metadata_field(index_type, index_value, metadata_field):
    '''
    index_type: string of the type of value you're finding metadata by.  Examples include 'cls' or 'raw_format'.
    index_value: value of the previous type.  For 'cls' a class object, for 'raw_format' a format string.
    metadata_field: string of the field type to retrieve.  This can be any of the values for index_type.
    '''
    return indexes[index_type][index_value][metadata_field]


def has_registered_class(cls_or_str, normalized=False):
    '''
    Takes either a class object or the string of a class name.
    normalized: True if the cls string is normalized.
        class: <class 'MySerializableClass'>
        class string: 'MySerializableClass'
        normalized class string: 'Serial_MySerializableClass' (or whatever PREFIX is)
    '''

    if not normalized:
        normalized_name = normalized_class_str(cls_or_str)
    else:
        normalized_name = cls_or_str
    normalized_cls_dicts = indexes['normalized_cls_str']
    return normalized_name in normalized_cls_dicts


def serialize(obj):
    stream = bitstring.BitStream()
    cls = obj.__class__

    cls_format = metadata_field('cls', cls, 'compact_format')
    attr_converters = metadata_field('cls', cls, 'attr_converters')
    fmt_converters = metadata_field('cls', cls, 'fmt_converters')

    for argstr in cls_format.split(','):
        format, name = argstr.split('=')
        data = getattr(obj, name)
        if has_registered_class(format, normalized=True):
            substream = serialize(data)
        else:
            # Check for converters for this object.
            # Attribute converters take precedence.
            if name in attr_converters:
                data = attr_converters[name][0](data)
            elif format in fmt_converters:
                data = fmt_converters[format][0](data)
            substream = bitstring.pack(format, data)
        stream.append(substream)
    return stream


def deserialize(cls, data, seek=True):
    kwargs = {}
    if seek:
        data.pos = 0

    cls_format = metadata_field('cls', cls, 'compact_format')
    attr_converters = metadata_field('cls', cls, 'attr_converters')
    fmt_converters = metadata_field('cls', cls, 'fmt_converters')

    for argstr in cls_format.split(','):
        format, name = argstr.split('=')
        if has_registered_class(format, normalized=True):
            subcls = metadata_field('normalized_cls_str', format, 'cls')
            kwargs[name] = deserialize(subcls, data, seek=False)
        else:
            value = data.read(format)
            # Check for converters for this object.
            # Attribute converters take precedence.
            if name in attr_converters:
                value = attr_converters[name][1](value)
            elif format in fmt_converters:
                value = fmt_converters[format][1](value)
            kwargs[name] = value
    return cls.deserialize(**kwargs)


def autoserialized(cls):
    '''The class must support an empty init function.'''
    attr_converters = getattr(cls, 'serial_attr_converters', None)
    fmt_converters = getattr(cls, 'serial_fmt_converters', None)
    register(
        cls, cls.serial_format,
        attr_converters=attr_converters,
        fmt_converters=fmt_converters
    )

    @classmethod
    def deserialize(cls, **kwargs):
        obj = cls()
        for attr in metadata_field('cls', cls, 'attrs'):
            setattr(obj, attr, kwargs.get(attr, None))
        return obj
    cls.deserialize = deserialize
    return cls


def serial_dict(obj, prefix='', dict=None):
    if dict is None:
        dict = collections.OrderedDict()

    fmt = metadata_field('cls', obj.__class__, 'compact_format')
    for argstr in fmt.split(','):
        format, attr_name = argstr.split('=')
        data = getattr(obj, attr_name)
        if has_registered_class(format, normalized=True):
            data_prefix = prefix + attr_name + '.'
            serial_dict(data, data_prefix, dict)
        else:
            # Just an attribute
            dict[prefix+attr_name] = data
    return dict
