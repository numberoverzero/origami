def init(*attrs):
    def fn(self, *args):
        for attr, arg in zip(attrs, args):
            setattr(self, attr, arg)
    return fn


def equals(*attrs):
    def eq(self, other):
        eq_ = lambda at: getattr(self, at) == getattr(other, at)
        eqs_ = map(eq_, attrs)
        return all(eqs_)
    return eq
