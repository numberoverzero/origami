import unittest
from pyserializable import serialized
from pyserializable.tests import equals, unique_serializer


class ConverterTests(unittest.TestCase):
    '''Unit tests for attribute and format converters'''

    def setUp(self):
        self.n, self.s = unique_serializer()

    def testEmptyConverters(self):
        '''Empty converters (None or {}) should be fine'''

        @serialized(self.n)
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
        '''Attribute converters should work on specified fields'''

        @serialized(self.n)
        class Blob(object):
            serial_format = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            serial_attr_converters = {'enabled': [int, bool]}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = True
        blob.r = 127
        blob.g = 128
        blob.b = 129

        data = self.s.serialize(blob)
        other_blob = self.s.deserialize(Blob, data)

        assert blob == other_blob

    def testSingleFmtConverter(self):
        '''Format converters should work on all fields with matching formats'''

        @serialized(self.n)
        class Blob(object):
            serial_format = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            serial_fmt_converters = {'uint:8': [int, str]}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = 1
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

        @serialized(self.n)
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
