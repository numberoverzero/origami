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

noop = lambda self, *a, **kw: None
passthrough = lambda v: v
