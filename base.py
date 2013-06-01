

def fold(obj):
    cls = obj.__class__
    if hasattr(cls, 'fold_metadata'):
        return cls.fold_metadata['crafter'].fold(obj)
    else:
        raise AttributeError("Couldn't find a crafter for object of type '{}'".format(cls.__name__))


def unfold(cls_or_obj, data):
    try:
        crafter = cls_or_obj.fold_metadata['crafter']
    except:
        try:
            crafter = cls_or_obj.__class__.fold_metadata['crafter']
        except:
            raise AttributeError("Couldn't find a crafter to unfold with.")
    return crafter.unfold(cls_or_obj, data)
