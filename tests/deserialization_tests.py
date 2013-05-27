import unittest
from pyserializable import Serializer
from pyserializable.tests import equals


class DeserializationTests(unittest.TestCase):
    '''Unit tests for basic deserialization'''

    def setUp(self):

        class Blob(object):
            serial_format = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            init_calls = 0

            def __init__(self):
                Blob.init_calls += 1

            def set_attrs(self, *values):
                for attr, value in zip('abcd', values):
                    setattr(self, attr, value)

            __eq__ = equals(*list('abcd'))

            @classmethod
            def deserialize(cls, instance, **kwargs):
                instance = instance or cls()
                for attr, value in kwargs.items():
                    setattr(instance, attr, value)
                return instance

        self.Blob = Blob

        serializer = Serializer()
        serializer.register(Blob, Blob.serial_format)

        self.s = serializer

    def testOjbectDeserialization(self):
        '''Deserialize into an object that already exists, not using the class's __init__ function'''

        blob = self.Blob()
        blob.set_attrs(1, 3, 7, 15)
        other_blob = self.Blob()
        serialized_blob = self.s.serialize(blob)

        self.s.deserialize(other_blob, serialized_blob)
        assert blob == other_blob

    def testClassDeserialization(self):
        '''Deserialize against a class, using the class's __init__ function'''

        blob = self.Blob()
        blob.set_attrs(1, 3, 7, 15)
        serialized_blob = self.s.serialize(blob)

        other_blob = self.s.deserialize(self.Blob, serialized_blob)
        assert blob == other_blob
