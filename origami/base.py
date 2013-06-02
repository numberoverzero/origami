from crafter import Crafter


def fold(obj, crafter='global'):
    crafter = Crafter(crafter)
    return crafter.fold(obj)


def unfold(cls_or_obj, data, crafter='global'):
    crafter = Crafter(crafter)
    return crafter.unfold(cls_or_obj, data)
