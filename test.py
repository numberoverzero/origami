from pyserializable import serialize, deserialize, autoserialized, serial_dict


def str_func(*arg_names):
    def str(self):
        cls_name = self.__class__.__name__

        def fmt_func(name):
            value = getattr(self, name)
            return '{}={}'.format(name, value)

        fmt_str = ', '.join(map(fmt_func, arg_names))
        return '{}({})'.format(cls_name, fmt_str)
    return str


@autoserialized
class Color:
    serial_format = 'r=uint:8, g=uint:8, b=uint:8, a=uint:8'
    __str__ = str_func('r', 'g', 'b', 'a')


@autoserialized
class Tile:
    #serial_format = 'uint:1=enabled, Color=color, uint:1=elite'
    serial_format = 'enabled=uint:1, color=Color, elite=uint:1'
    __str__ = str_func('enabled', 'color', 'elite')

t = Tile()
t.enabled = False
t.elite = True
t.color = Color()
t.color.r = 201
t.color.g = 202
t.color.b = 203
t.color.a = 204

data = serialize(t)

t2 = deserialize(Tile, data)

print(t)
print(t2)
