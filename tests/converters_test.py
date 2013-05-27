import unittest
from pyserializable import autoserializer, Serializer
from pyserializable.tests import equals


class ConverterTests(unittest.TestCase):
    '''Unit tests for attribute and format converters'''

    def setUp(self):
        self.s = Serializer()

    def testEmptyConverters(self):
        '''Empty converters (None or {}) should be fine'''

        @autoserializer(self.s)
        class Blob(object):
            serial_format = 'enabled=uint:1, alpha=uint:8'
            serial_attr_converters = None
            serial_fmt_converters = {}

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.s.serialize(blob)
        other_blob = self.s.deserialize(Blob, data)
        assert blob == other_blob

    def testSingleAttrConverter(self):
        '''Format converters should work on all fields with matching formats'''

        @autoserializer(self.s)
        class Blob(object):
            serial_format = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            serial_fmt_converters = {'uint:8': [int, str]}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = True
        blob.r = '127'
        blob.g = '128'
        blob.b = '129'

        data = self.s.serialize(blob)
        other_blob = self.s.deserialize(Blob, data)

        assert blob == other_blob

    def testAttrConvertersTakePrecedence(self):
        '''When a value is covered by both types of converters, only the attr converter should be used.'''

        def should_never_call(arg):
            '''If this function is called, then the fmt converter was used instead of the attr converter :('''
            assert False

        @autoserializer(self.s)
        class Blob(object):
            serial_format = 'enabled=uint:1'
            serial_attr_converters = {'enabled': [int, bool]}
            serial_fmt_converters = {'uint:1': [should_never_call] * 2}

            __eq__ = equals('enabled')

        blob = Blob()
        blob.enabled = True

        data = self.s.serialize(blob)
        other_blob = self.s.deserialize(Blob, data)

        assert blob == other_blob
