from origami.crafter import Crafter


def fold(obj, crafter='global'):
    '''
    Convenience method for folding an object with a specific Crafter.
    Default Crafter is 'global'
    '''
    return Crafter(crafter).fold(obj)


def unfold(cls_or_obj, data, crafter='global'):
    '''
    Convenience method for unfolding data according to a given class pattern or into a given object.
    Default Crafter is 'global'
    '''
    return Crafter(crafter).unfold(cls_or_obj, data)
