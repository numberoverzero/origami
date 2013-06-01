from bitfold.crafter import Crafter

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
        cls.fold_format,
        getattr(cls, 'fold_translators', {})
    )

    if hasattr(cls, 'unfold'):
        return cls

    @classmethod
    def unfold(cls, instance, **kwargs):
        if instance is None:
            instance = cls()
        for attr, fmt in cls.fold_metadata['fold_format']:
            try:
                setattr(instance, attr, kwargs[attr])
            except KeyError:
                raise AttributeError(_AUTO_MISSING_ATTR.format(attr))
        return instance
    cls.unfold = unfold

    return cls
