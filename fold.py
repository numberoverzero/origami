from bitfold.folder import folder

_AUTO_MISSING_ATTR = "Built-in unfold method expected value for attribute '{}' but found none."


def fold(obj):
    cls = obj.__class__
    if hasattr(cls, 'fold_metadata'):
        return cls.fold_metadata['folder'].fold(obj)
    else:
        raise AttributeError("Couldn't find a folder for object of type '{}'".format(cls.__name__))


def unfold(cls_or_obj, data):
    try:
        folder = cls_or_obj.fold_metadata['folder']
    except:
        try:
            folder = cls_or_obj.__class__.fold_metadata['folder']
        except:
            raise AttributeError("Couldn't find a folder to unfold with.")
    return folder.unfold(cls_or_obj, data)


def foldable(arg):
    if isinstance(arg, str):
        def class_decorator(cls):
            return _wrap_class(arg, cls)
        return class_decorator
    else:
        return _wrap_class(None, arg)


def _wrap_class(registered_name, cls):
    folder(registered_name).register_class(
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
