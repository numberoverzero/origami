import unittest
from pyserializable import serialized, serialize
from pyserializable.tests import init, unique_serializer
from bitstring import CreationError


class SerializationTests(unittest.TestCase):
    '''Unit tests for basic serialization validation and errors'''

    def setUp(self):
        name, self.s = unique_serializer()

        @serialized(name)
        class Blob(object):
            serial_format = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            __init__ = init(*list('abcd'))

        self.Blob = Blob

    def testSerializationLength(self):
        '''
        The length of the serialized data in bits should be the sum
        of the bit-widths of its class's serial_format field
        '''
        blob = self.Blob(1, 3, 7, 15)
        s = serialize(blob)

        blob2 = self.Blob(0, 0, 0, 0)
        s2 = serialize(blob2)

        assert len(s) == sum(range(5))
        assert len(s2) == sum(range(5))

    def testSerializationValueOverflow(self):
        '''
        When passing a value larger than the defined bit-width can contain,
        a CreationError should be thrown.
        '''

        blob = self.Blob(2**8, 1, 1, 1)
        try_serialize = lambda: serialize(blob)
        self.assertRaises(CreationError, try_serialize)

    def testSerializationMissingAttribute(self):
        '''
        When an object to be serialized is missing attributes named in
        it's class's serial_format string, an AttributeError is thrown.
        '''

        blob = self.Blob(0)
        try_serialize = lambda: serialize(blob)

        self.assertRaises(AttributeError, try_serialize)
