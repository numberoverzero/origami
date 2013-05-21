import collections
import bitstring


PREFIX = "Serial_"
indexes = {}
attributes = ['cls', 'cls_str', 'normalized_cls_str', 'raw_format', 'compact_format']

#  Build indexes into SerializationMetadata
for attr in attributes:
    indexes[attr] = {}


def register(cls, serial_format):
    metadata = SerializationMetadata(cls, serial_format)
    for attr, index in indexes.items():
        index[getattr(metadata, attr)] = metadata


class SerializationMetadata:
    def __init__(self, cls, raw_format):
        self.cls = cls
        self.cls_str = cls.__name__
        self.normalized_cls_str = PREFIX + self.cls_str

        self.raw_format = raw_format
        pieces = self.raw_format.split(',')
        compact_pieces = []
        for piece in pieces:
            name, format = [p.strip() for p in piece.split('=')]
            if format in indexes['cls_str']:
                compact_pieces.append('{}={}'.format(PREFIX+format, name))
            else:
                compact_pieces.append('{}={}'.format(format, name))
        compact_format = ','.join(compact_pieces)
        self.compact_format = compact_format

        formats = self.raw_format.split(',')
        attrs = [fmt.split('=')[0].strip() for fmt in formats]
        self.attrs = attrs


def serialize(obj):
    stream = bitstring.BitStream()
    cls = obj.__class__
    cls_format = indexes['cls'][cls].compact_format
    for argstr in cls_format.split(','):
        format, name = argstr.split('=')
        data = getattr(obj, name)
        if format in indexes['normalized_cls_str']:
            substream = serialize(data)
        else:
            substream = bitstring.pack(format, data)
        stream.append(substream)
    return stream


def deserialize(cls, data, seek=True):
    kwargs = {}
    if seek:
        data.pos = 0

    cls_format = indexes['cls'][cls].compact_format
    for argstr in cls_format.split(','):
        format, name = argstr.split('=')
        if PREFIX in format:
            subcls = indexes['normalized_cls_str'][format].cls
            kwargs[name] = deserialize(subcls, data, seek=False)
        else:
            kwargs[name] = data.read(format)
    return cls.deserialize(**kwargs)


def autoserialized(cls):
    '''The class must support an empty init function.'''
    register(cls, cls.serial_format)

    @classmethod
    def deserialize(cls, **kwargs):
        obj = cls()
        for attr in indexes['cls'][cls].attrs:
            setattr(obj, attr, kwargs.get(attr, None))
        return obj
    cls.deserialize = deserialize
    return cls


def serial_dict(obj, prefix='', dict=None):
    if dict is None:
        dict = collections.OrderedDict()

    fmt = indexes['cls'][obj.__class__].compact_format
    for argstr in fmt.split(','):
        format, attr_name = argstr.split('=')
        data = getattr(obj, attr_name)
        if format in indexes['normalized_cls_str']:
            # Format is registered as serializable, so data is an object to serialize
            data_prefix = prefix + attr_name + '.'
            serial_dict(data, data_prefix, dict)
        else:
            # Just an attribute
            dict[prefix+attr_name] = data
    return dict
