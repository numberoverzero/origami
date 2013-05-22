def str_func(*arg_names):
    '''For the given arg names, returns a function that prints the values of those attributes on the object.'''
    def str_(self):
        cls_name = self.__class__.__name__

        def fmt_func(name):
            value = getattr(self, name)
            return '{}={}'.format(name, str(value))

        fmt_str = ', '.join(map(fmt_func, arg_names))
        return '{}({})'.format(cls_name, fmt_str)
    return str_


def repr_func(*arg_names):
    '''For the given arg names, returns a function that prints the values of those attributes on the object.'''
    def repr_(self):
        cls_name = self.__class__.__name__

        def fmt_func(name):
            value = getattr(self, name)
            return '{}={}'.format(name, repr(value))

        fmt_str = ', '.join(map(fmt_func, arg_names))
        return '{}({})'.format(cls_name, fmt_str)
    return repr_
