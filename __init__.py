import bitstring

PREFIX = "Serial_"
class_formats = {}  # cls_obj => format w/replacement
format_classes = {}  # str(prefix+name) => cls


def is_registered(clsstr):
    return (PREFIX + clsstr) in format_classes


def replace_fmt(fmt):
    pieces = fmt.split(',')
    new_pieces = []
    for piece in pieces:
        #Color=color
        #uint:8=red
        pfmt, pname = [p.strip() for p in piece.split('=')]
        if is_registered(pfmt):
            new_pieces.append('{}={}'.format(PREFIX+pfmt, pname))
        else:
            new_pieces.append('{}={}'.format(pfmt, pname))
    return ','.join(new_pieces)


def register(cls):
    fmt = replace_fmt(cls.serial_format)
    class_formats[cls] = fmt
    format_classes[PREFIX + cls.__name__] = cls


def get_fmt(cls):
    return class_formats[cls]


def get_cls(arg_str):
    return format_classes[arg_str]


def deserialize(cls, data, seek=True):
    if seek:
        data.pos = 0
    fmt = get_fmt(cls)
    kwargs = {}
    for argstr in fmt.split(','):
        argfmt, argname = argstr.split('=')
        if PREFIX in argfmt:
            subcls = get_cls(argfmt)
            kwargs[argname] = deserialize(subcls, data, seek=False)
        else:
            kwargs[argname] = data.read(argfmt)
    return cls.deserialize(**kwargs)


def serialize(obj):
    stream = bitstring.BitStream()
    fmt = get_fmt(obj.__class__)
    for argstr in fmt.split(','):
        argfmt, argname = argstr.split('=')
        data = getattr(obj, argname)
        if PREFIX in argfmt:
            substream = serialize(data)
        else:
            substream = bitstring.pack(argfmt, data)
        stream.append(substream)
    return stream


def get_attrs(cls):
    attr_fmts = cls.serial_format.split(',')
    attr_names = [fmt.split('=')[1].strip() for fmt in attr_fmts]
    return attr_names


def autoserialized(cls):
    @classmethod
    def deserialize(cls, **kwargs):
        obj = cls()
        for attr in get_attrs(cls):
            setattr(obj, attr, kwargs.get(attr, None))
        return obj

    cls.deserialize = deserialize
    register(cls)
    return cls
