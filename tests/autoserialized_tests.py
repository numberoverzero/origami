import unittest
from pyserializable import autoserializer, Serializer


class AutoserializedTests(unittest.TestCase):
    '''Unit tests for the @autoserializer() decorator'''

    def setUp(self):

        @autoserializer(Serializer())
        class Blob(object):
            serial_format = 'n=uint:8'
            clsatr = "Some Value"
            init_calls = 0

            def __init__(self, n='empty'):
                self.n = n
                Blob.init_calls += 1

        self.Blob = Blob

    def testClassAttributesUnchanged(self):
        '''Autoserializing a class shouldn't modify any of its attributes'''
        blob = self.Blob('full')

        assert blob.n == 'full'
        assert blob.clsatr == "Some Value"
        assert self.Blob.clsatr == "Some Value"

    def testDeserializeMethodUsesDefaultInit(self):
        '''
        When None is passed to the deserialize method on the class,
        the default constructor should be called.
        '''
        data = {'n': 'full'}
        blob = self.Blob.deserialize(None, **data)

        assert blob.n == 'full'
        assert self.Blob.init_calls > 0

    def testDeserializeMethodUsesInstance(self):
        '''
        When an instance of the class is passed to deserialize,
        it should not call the constructor.
        '''
        data = {'n': 'full'}
        blob = self.Blob('empty')
        blob = self.Blob.deserialize(blob, **data)

        assert blob.n == 'full'
        assert self.Blob.init_calls == 1

    def testDeserializeExtraKwargs(self):
        '''
        Passing extra kwargs to the deserialize method on the class
        should be ok.
        '''
        data = {'n': 'full', 'junk': 'unused'}
        blob = self.Blob.deserialize(None, **data)

        assert blob.n == 'full'
        assert not hasattr(blob, 'junk')

    def testDeserializeMissingKwargs(self):
        '''
        Passing too few kwargs to the deserialize method on the class
        should raise an AttributeError.
        '''
        data = {'junk': 'unused'}
        deserialize = lambda: self.Blob.deserialize(None, **data)

        self.assertRaises(AttributeError, deserialize)
