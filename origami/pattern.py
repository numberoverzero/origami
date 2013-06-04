from origami.crafter import Crafter
from origami.exceptions import UnfoldingException


def pattern(crafter='global', unfold=True):
    '''
    Class decorator that handles most of the pattern learning machinery for a class.

    The decorated class should have the attribute _folds, and optionally _creases.

    crafter is a string indicating which crafter the class will be learned by, and defaults to 'global'

    If unfold is True, creates an "unfold" function on the class that constructs instances of the class from data
    unfolded by the Crafter.  The attributes that will be set are pulled from the class's _folds string.

    If the class's _folds attribute is a dictionary, uses the string found at _folds[creator].
    Passes _creases to the Crafter if defined, otherwise an empty dictionary.
    '''
    def wrap_class(cls):
        c = Crafter(crafter)

        if unfold:
            @classmethod
            def cls_unfold(cls, name, instance, **kwargs):
                if instance is None:
                    try:
                        instance = cls()
                    except TypeError:
                        raise UnfoldingException(cls, '__init__ method has 1 or more requires arguments')
                for attr, fmt in Crafter(name).patterns[cls]['folds']:
                    try:
                        setattr(instance, attr, kwargs[attr])
                    except KeyError:
                        raise UnfoldingException(instance, "missing expected attribute '{}'".format(attr))
                return instance
            cls.unfold = cls_unfold

        unfold_func = cls.unfold
        folds = getattr(cls, '_folds', '')
        creases = getattr(cls, '_creases', {})
        c.learn_pattern(cls, unfold_func, folds, creases)

        return cls
    return wrap_class
