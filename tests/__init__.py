from pyserializable import Serializer
import uuid

def init(*attrs):
    def fn(self, *args):
        for attr, arg in zip(attrs, args):
            setattr(self, attr, arg)
    return fn


def equals(*attrs):
    def eq(self, other):
        try:
            eq_ = lambda at: getattr(self, at) == getattr(other, at)
            return all(map(eq_, attrs))
        except AttributeError:
            return False
    return eq


def unique_serializer():
    name = str(uuid.uuid4())
    serializer = Serializer(name)
    return name, serializer
