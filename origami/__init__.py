import functools
from origami.crafter import Crafter, OrigamiException, UnfoldingException

__all__ = ['Crafter', 'pattern', 'fold', 'unfold', 'OrigamiException']


def fold(obj, crafter='global'):
    '''
    Convenience method for folding an object with a specific Crafter.
    Default Crafter is 'global'
    '''
    return Crafter(crafter).fold(obj)


def unfold(data, type, crafter='global'):
    '''
    Convenience method for unfolding data according to a
    given class pattern or into a given object.
    Default Crafter is 'global'
    '''
    return Crafter(crafter).unfold(data, type)


def pattern(cls=None, *, crafter='global', unfold=True):
    '''
    Class decorator that handles most of the pattern learning machinery for a class.

    The decorated class should have the attribute _folds, and optionally _creases.

    crafter is a string indicating which crafter the class will be learned by, and defaults to 'global'

    If unfold is True, creates an "unfold" function on the class that constructs instances of the class from data
    unfolded by the Crafter.  The attributes that will be set are pulled from the class's _folds string.

    If the class's _folds attribute is a dictionary, uses the string found at _folds[creator].
    Passes _creases to the Crafter if defined, otherwise an empty dictionary.
    '''
    if not cls:
        return functools.partial(pattern, crafter=crafter, unfold=unfold)

    c = Crafter(crafter)
    if unfold:
        _make_unfold_func(cls)
    unfold_func = cls.unfold
    folds = getattr(cls, 'folds', '')
    creases = getattr(cls, 'creases', {})
    c.learn_pattern(cls, unfold_func, folds, creases)
    return cls


def _make_unfold_func(cls):
    @classmethod
    def cls_unfold(cls, name, instance, **kwargs):
        if instance is None:
            try:
                instance = cls()
            except TypeError:
                raise UnfoldingException(cls, '__init__ method has 1 or more required arguments')
        try:
            for attr, fmt in Crafter(name).patterns[cls]['folds']:
                setattr(instance, attr, kwargs[attr])
        except KeyError:
            raise UnfoldingException(instance, "missing expected attribute '{}'".format(attr))
        return instance
    cls.unfold = cls_unfold
