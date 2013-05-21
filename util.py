import collections


def flatten(l, ltypes=collections.Sequence):
    l = list(l)
    while l:
        if isinstance(l[0], str):
            yield l.pop(0)
            continue
        while l and isinstance(l[0], ltypes):
            l[0:1] = l[0]
        if l:
            yield l.pop(0)


def getattrpath(obj, path):
    '''
    path is a dot-delimited chain of attributes to look up.
    getattrpath(my_object, 'a.b.c') returns my_object.a.b.c
    '''
    for attr in path.split('.'):
        obj = getattr(obj, attr)
    return obj


def prefix_keys(prefix, dict):
    for key, value in dict.items():
        yield prefix + key, value


def str_func(*arg_names):
    '''For the given arg names, returns a function that prints the values of those attributes on the object.'''
    def str(self):
        cls_name = self.__class__.__name__

        def fmt_func(name):
            value = getattr(self, name)
            return '{}={}'.format(name, value)

        fmt_str = ', '.join(map(fmt_func, arg_names))
        return '{}({})'.format(cls_name, fmt_str)
    return str


noop = lambda self, *a, **kw: None
passthrough = lambda v: v
