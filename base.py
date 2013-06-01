

def fold(obj):
    cls = obj.__class__
    try:
        return cls._default_crafter.fold(obj)
    except AttributeError:
        raise AttributeError("Couldn't find a crafter for object of type '{}'".format(cls.__name__))


def unfold(cls_or_obj, data):
    try:
        crafter = cls_or_obj._default_crafter
    except:
        try:
            crafter = cls_or_obj.__class__._default_crafter
        except:
            raise AttributeError("Couldn't find a crafter to unfold with.")
    return crafter.unfold(cls_or_obj, data)
