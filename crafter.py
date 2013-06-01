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

    def learn_pattern(self, cls, format, creases):
        if not creases:
            creases = {}
        origami_folds, bitstring_chunks = [], []
        name_creases = {}
        format_creases = {}

        for name, fmt in multidelim_generator(format, ',', '='):
            if name in creases:
                name_creases[name] = creases.pop(name)
            if fmt in creases:
                format_creases[fmt] = creases.pop(fmt)

            if fmt in self.patterns:
                subcls = self.patterns[fmt]
                subcls_fmt = self.patterns[subcls]['bitstring_format']
                bitstring_chunks.append(subcls_fmt)
                origami_folds.append((name, subcls))
            else:
                bitstring_chunks.append(fmt)
                origami_folds.append((name, fmt))

        bitstring_format = ','.join(bitstring_chunks)
        flat_count = len(bitstring_format.split(','))  # We have to do this after bitstring is joined because some
                                                       # pieces will be more than one piece (nested folding)
        fold_metadata = {
            'bitstring_format': bitstring_format,
            'origami_folds': origami_folds,
            'flat_count': flat_count,
            'name_creases': name_creases,
            'format_creases': format_creases
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
        name_creases = meta['name_creases']
        format_creases = meta['format_creases']

        for attr, fmt in meta['origami_folds']:
            try:
                data = getattr(obj, attr)
            except AttributeError:
                raise AttributeError(_MISSING_ATTR.format(obj.__class__.__name__, attr))

            if fmt in self.patterns:
                values.extend(self._get_flat_values(data))
            else:
                if attr in name_creases:
                    data = name_creases[attr]['fold'](data)
                elif fmt in format_creases:
                    data = format_creases[fmt]['fold'](data)
                values.append(data)
        return values

    def _obj_from_values(self, cls, instance, values, pos=0):
        kwargs = {}

        meta = self.patterns[cls]
        format = meta['origami_folds']
        name_creases = meta['name_creases']
        format_creases = meta['format_creases']

        for attr, fmt in format:
            if isinstance(fmt, str):
                value = values[pos]
                if attr in name_creases:
                    value = name_creases[attr]['unfold'](value)
                elif fmt in format_creases:
                    value = format_creases[fmt]['unfold'](value)
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
