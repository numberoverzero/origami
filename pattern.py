from origami.crafter import Crafter

_AUTO_MISSING_ATTR = "Built-in unfold method expected value for attribute '{}' but found none."


def pattern(crafter='global', default=True, unfold=True):
    def wrap_class(cls):
        c = Crafter(crafter)

        if unfold:
            @classmethod
            def cls_unfold(cls, name, instance, **kwargs):
                if instance is None:
                    instance = cls()
                for attr, fmt in Crafter(name).patterns[cls]['folds']:
                    try:
                        setattr(instance, attr, kwargs[attr])
                    except KeyError:
                        raise AttributeError(_AUTO_MISSING_ATTR.format(attr))
                return instance
            cls.unfold = cls_unfold

        unfold_func = cls.unfold
        folds = cls.origami_folds
        creases = getattr(cls, 'origami_creases', {})

        c.learn_pattern(cls, unfold_func, folds, creases)

        if default:
            cls._crafter = c

        return cls
    return wrap_class
