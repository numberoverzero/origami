from pyserializable import Serializer, autoserializer
from pyserializable.util import repr_func

serializer = Serializer()


@autoserializer(serializer)
class Color(object):
    serial_format = 'r=uint:8, g=uint:8, b=uint:8, a=uint:8'
    serial_attr_converters = {'r': [int, str]}
    __repr__ = repr_func('r', 'g', 'b', 'a')


@autoserializer(serializer)
class Tile(object):
    serial_format = 'enabled=uint:1, color=Color, elite=uint:1'
    serial_fmt_converters = {'uint:1': [int, bool]}
    __repr__ = repr_func('enabled', 'color', 'elite')

t = Tile()
t.enabled = False
t.elite = True
t.color = Color()
t.color.r = '201'
t.color.g = 202
t.color.b = 203
t.color.a = 204

data = serializer.serialize(t)

# Deserialize based on class
t2 = serializer.deserialize(Tile, data)

#Deserialize into existing instance
t3 = Tile()
serializer.deserialize(t3, data)

print(t)
print(t2)
print(t3)
