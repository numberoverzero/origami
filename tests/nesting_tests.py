import unittest
from pyserializable import autoserializer, Serializer
from pyserializable.tests import equals


class NestingTests(unittest.TestCase):
    '''Unit tests for nested serialization'''

    def setUp(self):
        self.s = Serializer()
        self.serialized = autoserializer(self.s)

    def testSingleNesting(self):

        @self.serialized
        class Address(object):
            serial_format = 'house_number=uint:7'

            __eq__ = equals('house_number')

        @self.serialized
        class Person(object):
            serial_format = 'age=uint:10, address=Address, alive=uint:1'

            __eq__ = equals('age', 'address', 'alive')

        address = Address()
        address.house_number = 16
        person = Person()
        person.age = 5
        person.alive = 1
        person.address = address

        data = self.s.serialize(person)
        other_person = self.s.deserialize(Person, data)

        assert person == other_person
