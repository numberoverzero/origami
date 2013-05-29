import unittest
from pyserializable import Serializer
from bitstring import CreationError


class SerializationTests(unittest.TestCase):
    '''Unit tests for basic serialization validation and errors'''

    def setUp(self):

        class Blob(object):
            serial_format = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'

            def set_attrs(self, *values):
                for attr, value in zip('abcd', values):
                    setattr(self, attr, value)
        self.Blob = Blob

        serializer = Serializer()
        self.serialize = lambda obj: serializer.serialize(obj)
        serializer.register(Blob, Blob.serial_format)

    def testSerializationLength(self):
        '''
        The length of the serialized data in bits should be the sum
        of the bit-widths of its class's serial_format field
        '''
        blob = self.Blob()
        blob.set_attrs(1, 3, 7, 15)
        s = self.serialize(blob)

        blob2 = self.Blob()
        blob2.set_attrs(0, 0, 0, 0)
        s2 = self.serialize(blob2)

        assert len(s) == sum(range(5))
        assert len(s2) == sum(range(5))

    def testSerializationValueOverflow(self):
        '''
        When passing a value larger than the defined bit-width can contain,
        a CreationError should be thrown.
        '''

        blob = self.Blob()
        blob.set_attrs(2**8, 1, 1, 1)
        serialize = lambda: self.serialize(blob)

        self.assertRaises(CreationError, serialize)

    def testSerializationMissingAttribute(self):
        '''
        When an object to be serialized is missing attributes named in
        it's class's serial_format string, an AttributeError is thrown.
        '''

        blob = self.Blob()
        blob.set_attrs(0)
        serialize = lambda: self.serialize(blob)

        self.assertRaises(AttributeError, serialize)
