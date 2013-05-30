import unittest
from pyserializable import serialized, serialize, deserialize
from pyserializable.tests import equals, init, unique_serializer


class DeserializationTests(unittest.TestCase):
    '''Unit tests for basic deserialization'''

    def setUp(self):
        name, self.s = unique_serializer()

        @serialized(name)
        class Blob(object):
            serial_format = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            __init__ = init(*list('abcd'))
            __eq__ = equals(*list('abcd'))

            @classmethod
            def deserialize(cls, instance, **kwargs):
                instance = instance or cls()
                for attr, value in kwargs.items():
                    setattr(instance, attr, value)
                return instance

        self.Blob = Blob

    def testOjbectDeserialization(self):
        '''Deserialize into an object that already exists, not using the class's __init__ function'''

        blob = self.Blob(1, 3, 7, 15)
        other_blob = self.Blob()
        serialized_blob = self.s.serialize(blob)

        self.s.deserialize(other_blob, serialized_blob)
        assert blob == other_blob

    def testClassDeserialization(self):
        '''Deserialize against a class, using the class's __init__ function'''

        blob = self.Blob(1, 3, 7, 15)
        serialized_blob = self.s.serialize(blob)

        other_blob = self.s.deserialize(self.Blob, serialized_blob)
        assert blob == other_blob

    def testClassSerializerAttribute(self):
        '''serialize and deserialize should work with the class's serial_metadata attribute'''

        blob = self.Blob(1, 3, 7, 15)
        s = serialize(blob)

        other_blob = deserialize(self.Blob, s)

        some_other_blob = self.Blob('wat', 'oh', 'god', 'no')
        deserialize(some_other_blob, s)

        assert blob == other_blob
        assert blob == some_other_blob
