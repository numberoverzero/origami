from crafter import Crafter


def fold(obj):
    cls = obj.__class__
    try:
        return cls._crafter.fold(obj)
    except AttributeError:
        raise AttributeError("Couldn't find a crafter for object of type '{}'".format(cls.__name__))


def unfold(cls_or_obj, data, crafter='global'):
    if crafter is not None:
        crafter = Crafter(crafter)
    else:
        try:
            crafter = cls_or_obj._crafter
        except:
            try:
                crafter = cls_or_obj.__class__._crafter
            except:
                raise AttributeError("Couldn't find a crafter to unfold with.")
    return crafter.unfold(cls_or_obj, data)
