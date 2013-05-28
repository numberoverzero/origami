from pyserializable import Serializable, serialize, deserialize, f


uint8 = lambda: f(format='uint:8', default=0)
boolean = lambda: f(format='uint:1', default=False,
                    to_serial=int, from_serial=bool)


class Color(Serializable):
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
    r = uint8()
    g = uint8()
    b = uint8()
    a = uint8()


class Tile(Serializable):
    enabled = boolean()
    color = f(Color)(122, 123, 124, 125)
    elite = boolean()

t = Tile()
print("Original tile:")
print(t)
print()

t.enabled = True
t.color.g = t.color.a = 100
print("Tile modified (using True instead of 1 for bool field)")
print(t)
print()

s = serialize(t)
print("Serialized tile data:")
print(s.bin)
print()


t2 = Tile()
print("Created new Tile (t2) to deserialize into:")
print(t2)
print()

deserialize(t2, s)
print("Deserialized tile data into t2.")
print("The following should be equal:")
print(t)
print(t2)
print()
