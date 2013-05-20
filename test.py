from pyserializable import Serializable, serialize, deserialize
from pyserializable.field import field


class Color(Serializable):
    r = field(format='uint:8', default=0)
    g = field(format='uint:8', default=0)
    b = field(format='uint:8', default=0)
    a = field(format='uint:8', default=0)


class Tile(Serializable):
    enabled = field(format='uint:1', default=False, to_serial=int, from_serial=bool)
    color = field(Color)
    elite = field(format='uint:1', default=False, to_serial=int, from_serial=bool)


t = Tile()
print(t)
t.enabled = True
t.color.g = t.color.a = 100

s = serialize(t)
t2 = Tile()
deserialize(t2, s)
print(t)
print(t2)
