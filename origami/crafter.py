from .util import multidelim_generator, validate_bitstring_format
import bitstring
import collections


class OrigamiException(Exception):
    pass


class InvalidPatternClassException(OrigamiException):
    def __init__(self, cls, reason):
        message = "Invalid pattern class '{}': ".format(cls) + reason
        OrigamiException.__init__(self, message)


class InvalidFoldFormatException(OrigamiException):
    def __init__(self, fold, reason):
        message = "Invalid fold '{}': ".format(fold) + reason
        OrigamiException.__init__(self, message)


class InvalidCreaseFormatException(OrigamiException):
    def __init__(self, crease, reason):
        message = "Invalid crease '{}': ".format(crease) + reason
        OrigamiException.__init__(self, message)


class FoldingException(OrigamiException):
    def __init__(self, obj, reason):
        message = "Failed to fold '{}': ".format(obj) + reason
        OrigamiException.__init__(self, message)


class UnfoldingException(OrigamiException):
    def __init__(self, obj, reason):
        message = "Failed to unfold '{}': ".format(obj) + reason
        OrigamiException.__init__(self, message)

_crafters = {}


class Crafter(object):
    '''
    Used for folding and unfolding patterns.
    '''
    def __new__(cls, name='global'):
        '''
        Crafters are uniquely identified by their name.
        '''
        if name not in _crafters:
            c = _crafters[name] = super(Crafter, cls).__new__(cls)
            c.name = name
            c.patterns = {}
        return _crafters[name]

    def __repr__(self, *args, **kwargs):
        return "Crafter('{}')".format(self.name)

    def learn_pattern(self, cls, unfold_func, folds, creases):
        '''
        cls - The class to learn
        unfold_func - A function that takes (crafter_name, instance, **kwargs) where crafter name is a string
            of the Crafter unfolding the object, instance is an instance of the cls or None, and kwargs is a dictionary
            where each key corresponds to the same key in folds.
        folds - string of formats to fold attributes of an instance with.  If this is a dictionary, its keys should be
            Crafter names, and the corresponding value a fold string.  If there is no key for the name of the Crafter
            that is learning the pattern, raises InvalidFoldFormatException.
        creases - creases is an optional dictionary whose keys are a mix of fold keys and fold formats.  If the key
            is a fold format, it may be a literal bitstring format, or a custom format that maps to a bitstring format.
            Each value should be a dictionary containing functinos for the keys 'fold' and 'unfold'.  These functions
            should take a single argument and return a single argument.  They will be called during folding and
            unfolding respectively, when getting or setting the particular attr on the instance of cls.  If the crease
            is a custom format that maps to a bitstring format, it must provide an additional key 'fmt' which is a valid
            bitstring format to use in place of the the literal key.  Name creases will always be used instead of format
            creases when both apply to a particular name, format fold pair.

            Example creases:

            # Used on a format, such as 'enabled=bool'
            # Doesn't need 'fmt' because bool is a bitstring format
            creases = {'bool': {'fold': my_bool_fold_func, 'unfold': my_bool_unfold_func}}

            # Used on a key, as in 'my_attr=uint:8'
            creases = {'my_attr': {'fold': fold_attr_func, 'unfold': unfold_attr_func}}

            #Custom format, as in 'enabled=my_bool'
            creases = {'bool': {'fmt': bool, fold': my_bool_fold_func, 'unfold': my_bool_unfold_func}}
        '''
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
        if isinstance(folds, collections.Mapping):
            try:
                folds = folds[self.name]
            except KeyError:
                raise InvalidFoldFormatException(folds, "No folds found for Crafter with name '{}'".format(self.name))
        for name, crease in creases.items():
            if 'fold' not in crease:
                raise InvalidCreaseFormatException(name, "Custom creases must specify a fold method")
            if 'unfold' not in crease:
                raise InvalidCreaseFormatException(name, "Custom creases must specify an unfold method")

        for name, fmt in multidelim_generator(folds, ',', '='):
            if name in creases:
                name_creases[name] = creases[name]
            if fmt in creases:
                format_creases[fmt] = creases[fmt]

            if fmt in self.patterns:
                subcls = self.patterns[fmt]
                subcls_fmt = self.patterns[subcls]['bitstring_format']
                bitstring_chunks.append(subcls_fmt)
                processed_folds.append((name, subcls))
            elif validate_bitstring_format(fmt):
                bitstring_chunks.append(fmt)
                processed_folds.append((name, fmt))
            elif fmt in format_creases:
                # This crease must have a 'fmt' key that defines a valid bitstring format.
                # This cannot refer to learned patterns because only one value is passed to the crease's fold/unfold
                # methods, and that wouldn't make since for a pattern with (potentially) more than one bitstring value.
                # Put the crease value for 'fmt' in the bitstring_chunks instead of the literal fmt string.
                try:
                    real_fmt = format_creases[fmt]['fmt']
                except KeyError:
                    raise InvalidCreaseFormatException(fmt, "Custom creases require a valid bistring format under the key 'fmt'.")
                if not validate_bitstring_format(real_fmt):
                    raise InvalidCreaseFormatException(fmt, 'Custom creases fmt not a known pattern or valid bitstring format.')
                bitstring_chunks.append(real_fmt)
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
        '''Fold the object into a BitString according to its pattern's folds and creases.'''
        try:
            fmt = self.patterns[obj.__class__]['bitstring_format']
        except KeyError:
            raise FoldingException(obj, "Unknown pattern class '{}'.".format(obj.__class__))

        values = self._get_flat_values(obj)

        try:
            return bitstring.pack(fmt, *values)
        except bitstring.CreationError as e:
            raise FoldingException(obj, str(e))
        except ValueError as e:
            raise FoldingException(obj, str(e))

    def unfold(self, data, type):
        '''
        Unfold the object (or return a new instance)
        from a BitString according to its pattern's folds and creases.
        '''
        cls, instance = self._get_cls_obj(type)
        fmt = self.patterns[cls]['bitstring_format']
        try:
            values = data.readlist(fmt)
        except bitstring.ReadError as e:
            raise UnfoldingException(type, e.msg)
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
                raise FoldingException(
                    obj, "missing expected attribute '{}'".format(attr))

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
        # Instance
        if cls_or_obj.__class__ in self.patterns:
            instance = cls_or_obj
            cls = instance.__class__
        # Class or string
        elif cls_or_obj in self.patterns:
            if isinstance(cls_or_obj, str):
                cls = self.patterns[cls_or_obj]
            else:
                cls = cls_or_obj
            instance = None
        # Unknown
        else:
            raise UnfoldingException(cls_or_obj, "Unknown object or pattern class '{}'.".format(cls_or_obj))
        return cls, instance
