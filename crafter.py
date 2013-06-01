from origami.util import multidelim_generator
import bitstring
import uuid

_MISSING_ATTR = "'{}' object was missing expected attribute '{}'"
_global_crafter_id = str(uuid.uuid4())
_crafters = {}


class Crafter(object):
    def __new__(cls, name=None):
        if not name:
            name = _global_crafter_id
        if name not in _crafters:
            c = _crafters[name] = super(Crafter, cls).__new__(cls)
            c.name = name
            c.patterns = {}
        return _crafters[name]

    def learn_pattern(self, cls, format, translators):
        if not translators:
            translators = {}
        fold_format, bitstring_chunks = [], []
        name_translators = {}
        format_translators = {}

        for name, fmt in multidelim_generator(format, ',', '='):
            if name in translators:
                name_translators[name] = translators.pop(name)
            if fmt in translators:
                format_translators[fmt] = translators.pop(fmt)

            if fmt in self.patterns:
                subcls = self.patterns[fmt]
                subcls_fmt = self.patterns[subcls]['bitstring_format']
                bitstring_chunks.append(subcls_fmt)
                fold_format.append((name, subcls))
            else:
                bitstring_chunks.append(fmt)
                fold_format.append((name, fmt))

        bitstring_format = ','.join(bitstring_chunks)
        flat_count = len(bitstring_format.split(','))  # We have to do this after bitstring is joined because some
                                                       # pieces will be more than one piece (nested folding)
        fold_metadata = {
            'bitstring_format': bitstring_format,
            'fold_format': fold_format,
            'flat_count': flat_count,
            'name_translators': name_translators,
            'format_translators': format_translators
        }
        self.patterns[cls] = fold_metadata
        self.patterns[cls.__name__] = cls
        if not getattr(cls, '_default_crafter', None):
            cls._default_crafter = self

    def fold(self, obj):
        values = self._get_flat_values(obj)
        fmt = self.patterns[obj.__class__]['bitstring_format']
        return bitstring.pack(fmt, *values)

    def unfold(self, cls_or_obj, data, seek=True):
        cls, instance = self._get_cls_obj(cls_or_obj)
        fmt = self.patterns[cls]['bitstring_format']
        values = data.unpack(fmt)
        return self._obj_from_values(cls, instance, values, pos=0)

    def _get_flat_values(self, obj):
        values = []

        meta = self.patterns[obj.__class__]
        name_translators = meta['name_translators']
        format_translators = meta['format_translators']

        for attr, fmt in meta['fold_format']:
            try:
                data = getattr(obj, attr)
            except AttributeError:
                raise AttributeError(_MISSING_ATTR.format(obj.__class__.__name__, attr))

            if fmt in self.patterns:
                values.extend(self._get_flat_values(data))
            else:
                if attr in name_translators:
                    data = name_translators[attr]['fold'](data)
                elif fmt in format_translators:
                    data = format_translators[fmt]['fold'](data)
                values.append(data)
        return values

    def _obj_from_values(self, cls, instance, values, pos=0):
        kwargs = {}

        meta = self.patterns[cls]
        format = meta['fold_format']
        name_translators = meta['name_translators']
        format_translators = meta['format_translators']

        for attr, fmt in format:
            if isinstance(fmt, str):
                value = values[pos]
                if attr in name_translators:
                    value = name_translators[attr]['unfold'](value)
                elif fmt in format_translators:
                    value = format_translators[fmt]['unfold'](value)
                offset = 1
            elif fmt in self.patterns:
                value = self._obj_from_values(fmt, None, values, pos=pos)
                offset = self.patterns[fmt]['flat_count']
            kwargs[attr] = value
            pos += offset
        return cls.unfold(self.name, instance, **kwargs)

    def _get_cls_obj(self, cls_or_obj):
        instance = None

        # Class or string
        if cls_or_obj in self.patterns:
            if isinstance(cls_or_obj, str):
                cls = self.patterns[cls_or_obj]
            else:
                cls = cls_or_obj
        #Instance
        elif cls_or_obj.__class__ in self.patterns:
            cls = cls_or_obj.__class__
            instance = cls_or_obj
        else:
            raise ValueError("Don't know how to unfold {}".format(cls_or_obj))
        return cls, instance
