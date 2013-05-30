import unittest
from pyserializable import serialized, serialize, deserialize
from pyserializable.tests import equals, unique_serializer

class NestingTests(unittest.TestCase):
    '''Unit tests for nested serialization'''

    def setUp(self):
        self.n, s = unique_serializer()

    def testSingleNesting(self):

        @serialized(self.n)
        class Address(object):
            serial_format = 'house_number=uint:7'

            __eq__ = equals('house_number')

        @serialized(self.n)
        class Person(object):
            serial_format = 'age=uint:10, address=Address, alive=uint:1'

            __eq__ = equals('age', 'address', 'alive')

        address = Address()
        address.house_number = 16
        person = Person()
        person.age = 5
        person.alive = 1
        person.address = address

        data = serialize(person)
        other_person = deserialize(Person, data)

        assert person == other_person
