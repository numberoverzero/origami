from origami.crafter import Crafter

_AUTO_MISSING_ATTR = "Built-in unfold method expected value for attribute '{}' but found none."


def pattern(arg):
    if isinstance(arg, str):
        def class_decorator(cls):
            return _wrap_class(arg, cls)
        return class_decorator
    else:
        return _wrap_class(None, arg)


def _wrap_class(name, cls):
    Crafter(name).learn_pattern(
        cls,
        cls.origami_folds,
        getattr(cls, 'origami_creases', {})
    )

    if hasattr(cls, 'unfold'):
        return cls

    @classmethod
    def unfold(cls, crafter_name, instance, **kwargs):
        if instance is None:
            instance = cls()
        for attr, fmt in Crafter(crafter_name).patterns[cls]['origami_folds']:
            try:
                setattr(instance, attr, kwargs[attr])
            except KeyError:
                raise AttributeError(_AUTO_MISSING_ATTR.format(attr))
        return instance
    cls.unfold = unfold

    return cls
