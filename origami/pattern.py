from origami.crafter import Crafter
from origami.exceptions import UnfoldingException


def pattern(crafter='global', unfold=True):
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
        folds = getattr(cls, 'origami_folds', '')
        creases = getattr(cls, 'origami_creases', {})
        c.learn_pattern(cls, unfold_func, folds, creases)

        return cls
    return wrap_class
