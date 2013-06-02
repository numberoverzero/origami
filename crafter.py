from origami.util import multidelim_generator, validate_bitstring_format
from origami.exceptions import (
    InvalidPatternClassException,
    InvalidFoldFormatException,
    FoldingException,
    UnfoldingException
)
import bitstring

_crafters = {}


class Crafter(object):
    def __new__(cls, name='global'):
        if name not in _crafters:
            c = _crafters[name] = super(Crafter, cls).__new__(cls)
            c.name = name
            c.patterns = {}
        return _crafters[name]

    def learn_pattern(self, cls, unfold_func, folds, creases):
        if not cls:
            raise InvalidPatternClassException(cls, "Must be class object.")
        if cls.__name__ in self.patterns:
            raise InvalidPatternClassException(cls, "Crafter {} already learned it.".format(self.name))
        processed_folds, bitstring_chunks = [], []

        creases = creases or {}
        name_creases = {}
        format_creases = {}

        if not folds:
            raise InvalidFoldFormatException(folds, 'Nothing to fold!')

        for name, fmt in multidelim_generator(folds, ',', '='):
            if name in creases:
                name_creases[name] = creases.pop(name)
            if fmt in creases:
                format_creases[fmt] = creases.pop(fmt)

            if fmt in self.patterns:
                subcls = self.patterns[fmt]
                subcls_fmt = self.patterns[subcls]['bitstring_format']
                bitstring_chunks.append(subcls_fmt)
                processed_folds.append((name, subcls))
            elif validate_bitstring_format(fmt):
                bitstring_chunks.append(fmt)
                processed_folds.append((name, fmt))
            else:
                raise InvalidFoldFormatException(fmt, 'Not a known pattern or valid bitstring format.')

        bitstring_format = ','.join(bitstring_chunks)
        flat_count = len(bitstring_format.split(','))  # We have to do this after bitstring is joined because some
                                                       # pieces will be more than one piece (nested folding)
        fold_metadata = {
            'bitstring_format': bitstring_format,
            'folds': processed_folds,
            'unfold': unfold_func,
            'flat_count': flat_count,
            'name_creases': name_creases,
            'format_creases': format_creases
        }
        self.patterns[cls] = fold_metadata
        self.patterns[cls.__name__] = cls

    def fold(self, obj):
        try:
            fmt = self.patterns[obj.__class__]['bitstring_format']
        except KeyError:
            raise FoldingException(obj, "Unknown pattern class '{}'.".format(obj.__class__))

        values = self._get_flat_values(obj)

        try:
            return bitstring.pack(fmt, *values)
        except ValueError as e:
            raise FoldingException(obj, e.message)

    def unfold(self, cls_or_obj, data, seek=True):
        cls, instance = self._get_cls_obj(cls_or_obj)
        fmt = self.patterns[cls]['bitstring_format']
        try:
            values = data.unpack(fmt)
        except bitstring.ReadError as e:
            raise UnfoldingException(cls_or_obj, e.msg)
        return self._obj_from_values(cls, instance, values, pos=0)

    def _get_flat_values(self, obj):
        values = []

        meta = self.patterns[obj.__class__]
        name_creases = meta['name_creases']
        format_creases = meta['format_creases']

        for attr, fmt in meta['folds']:
            try:
                data = getattr(obj, attr)
            except AttributeError:
                raise FoldingException(obj, "missing expected attribute '{}'".format(attr))

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
        format = meta['folds']
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
        return self.patterns[cls]['unfold'](self.name, instance, **kwargs)

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
            raise UnfoldingException(cls_or_obj, "Unknown object or pattern class '{}'.".format(cls_or_obj))
        return cls, instance
