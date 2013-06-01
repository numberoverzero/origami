from bitfold import Crafter, pattern, fold, unfold
from bitstring import CreationError
import unittest
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


def unique_crafter():
    name = str(uuid.uuid4())
    _crafter = Crafter(name)
    return name, _crafter


class GlobalFolderTests(unittest.TestCase):
    '''Unit tests for the @pattern decorator (using global crafter)'''

    def setUp(self):
        @pattern
        class Blob(object):
            fold_format = 'n=uint:8'
            clsatr = "Some Value"
            init_calls = 0

            def __init__(self, n='empty'):
                self.n = n
                Blob.init_calls += 1

            __eq__ = equals('n')

        self.Blob = Blob

    def testClassAttributesUnchanged(self):
        '''@pattern decorator shouldn't modify existing class attributes'''
        blob = self.Blob('full')

        assert blob.n == 'full'
        assert blob.clsatr == "Some Value"
        assert self.Blob.clsatr == "Some Value"

    def testUnfoldMethodUsesDefaultInit(self):
        '''
        When None is passed to the unfold method on the class, the default constructor should be called.
        '''
        data = {'n': 'full'}
        blob = self.Blob.unfold(None, **data)

        assert blob.n == 'full'
        assert self.Blob.init_calls > 0

    def testUnfoldMethodUsesInstance(self):
        '''
        When an instance of the class is passed to unfold, it should not call the constructor.
        '''
        data = {'n': 'full'}
        blob = self.Blob('empty')
        blob = self.Blob.unfold(blob, **data)

        assert blob.n == 'full'
        assert self.Blob.init_calls == 1

    def testUnfoldExtraKwargs(self):
        '''
        Passing extra kwargs to the unfold method on the class should be ok.
        '''
        data = {'n': 'full', 'junk': 'unused'}
        blob = self.Blob.unfold(None, **data)

        assert blob.n == 'full'
        assert not hasattr(blob, 'junk')

    def testUnfoldMissingKwargs(self):
        '''
        Passing too few kwargs to the unfold method on the class should raise an AttributeError.
        '''
        data = {'junk': 'unused'}
        try_unfold = lambda: self.Blob.unfold(None, **data)

        self.assertRaises(AttributeError, try_unfold)


class TranslatorTests(unittest.TestCase):
    '''Unit tests for attribute and format translators'''

    def setUp(self):
        self.n, self.f = unique_crafter()

    def testNoTranslators(self):
        '''No fold_translators attribute defined'''

        @pattern(self.n)
        class Blob(object):
            fold_format = 'enabled=uint:1, alpha=uint:8'

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.f.fold(blob)
        other_blob = self.f.unfold(Blob, data)
        assert blob == other_blob

    def testTranslatorsIsNone(self):
        '''fold_translators attribute is None'''

        @pattern(self.n)
        class Blob(object):
            fold_format = 'enabled=uint:1, alpha=uint:8'
            fold_translators = None

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.f.fold(blob)
        other_blob = self.f.unfold(Blob, data)
        assert blob == other_blob

    def testTranslatorsIsEmpty(self):
        '''fold_translators attribute is {}'''

        @pattern(self.n)
        class Blob(object):
            fold_format = 'enabled=uint:1, alpha=uint:8'
            fold_translators = {}

            __eq__ = equals('enabled', 'alpha')

        blob = Blob()
        blob.enabled = 1
        blob.alpha = 127

        data = self.f.fold(blob)
        other_blob = self.f.unfold(Blob, data)
        assert blob == other_blob

    def testSingleNamedTranslator(self):
        '''Named translators should work on specified fields'''

        @pattern(self.n)
        class Blob(object):
            fold_format = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            fold_translators = {'enabled': {'fold': int, 'unfold': bool}}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = True
        blob.r = 127
        blob.g = 128
        blob.b = 129

        data = self.f.fold(blob)
        other_blob = self.f.unfold(Blob, data)

        assert blob == other_blob

    def testSingleFormatTranslator(self):
        '''Format translators should work on all fields with matching formats'''

        @pattern(self.n)
        class Blob(object):
            fold_format = 'enabled=uint:1, r=uint:8, g=uint:8, b=uint:8'
            fold_translators = {'uint:8': {'fold': int, 'unfold': str}}

            __eq__ = equals('enabled', 'r', 'g', 'b')

        blob = Blob()
        blob.enabled = 1
        blob.r = '127'
        blob.g = '128'
        blob.b = '129'

        data = self.f.fold(blob)
        other_blob = self.f.unfold(Blob, data)

        assert blob == other_blob

    def testNamedTranslatorsTakePrecedence(self):
        '''When a value is covered by both types of translators, only the name translator should be used.'''

        def never_call(arg):
            assert False

        @pattern(self.n)
        class Blob(object):
            fold_format = 'enabled=uint:1'
            fold_translators = {
                'enabled': {'fold': int, 'unfold': bool},
                'uint:1': {'fold': never_call, 'unfold': never_call}
            }

            __eq__ = equals('enabled')

        blob = Blob()
        blob.enabled = True

        data = self.f.fold(blob)
        other_blob = self.f.unfold(Blob, data)

        assert blob == other_blob


class NestingTests(unittest.TestCase):
    '''Unit tests for nested folding'''

    def setUp(self):
        self.n, f = unique_crafter()

    def testSingleNesting(self):

        @pattern(self.n)
        class Address(object):
            fold_format = 'house_number=uint:7'

            __eq__ = equals('house_number')

        @pattern(self.n)
        class Person(object):
            fold_format = 'age=uint:10, address=Address, alive=uint:1'

            __eq__ = equals('age', 'address', 'alive')

        address = Address()
        address.house_number = 16
        person = Person()
        person.age = 5
        person.alive = 1
        person.address = address

        data = fold(person)
        other_person = unfold(Person, data)

        assert person == other_person


class UnfoldTests(unittest.TestCase):
    '''Unit tests for basic unfolding'''

    def setUp(self):
        name, self.f = unique_crafter()

        @pattern(name)
        class Blob(object):
            fold_format = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            __init__ = init(*list('abcd'))
            __eq__ = equals(*list('abcd'))

            @classmethod
            def unfold(cls, instance, **kwargs):
                instance = instance or cls()
                for attr, value in kwargs.items():
                    setattr(instance, attr, value)
                return instance

        self.Blob = Blob

    def testOjbectUnfolding(self):
        '''Unfold into an object that already exists, not using the class's __init__ function'''

        blob = self.Blob(1, 3, 7, 15)
        other_blob = self.Blob()
        folded_blob = self.f.fold(blob)

        self.f.unfold(other_blob, folded_blob)
        assert blob == other_blob

    def testClassUnfolding(self):
        '''Unfold against a class, using the class's __init__ function'''

        blob = self.Blob(1, 3, 7, 15)
        folded_blob = self.f.fold(blob)

        other_blob = self.f.unfold(self.Blob, folded_blob)
        assert blob == other_blob

    def testClassFoldAttribute(self):
        '''fold and unfold should work with the class's fold_metadata attribute'''

        blob = self.Blob(1, 3, 7, 15)
        s = fold(blob)

        other_blob = unfold(self.Blob, s)

        some_other_blob = self.Blob('wat', 'oh', 'god', 'no')
        unfold(some_other_blob, s)

        assert blob == other_blob
        assert blob == some_other_blob


class SerializationTests(unittest.TestCase):
    '''Unit tests for basic serialization validation and errors'''

    def setUp(self):
        name, f = unique_crafter()

        @pattern(name)
        class Blob(object):
            fold_format = 'a=uint:1, b=uint:2, c=uint:3, d=uint:4'
            __init__ = init(*list('abcd'))

        self.Blob = Blob

    def testFoldedLength(self):
        '''
        The length of the folded data in bits should be the sum
        of the bit-widths of its class's fold_format field
        '''
        blob = self.Blob(1, 3, 7, 15)
        s = fold(blob)

        blob2 = self.Blob(0, 0, 0, 0)
        s2 = fold(blob2)

        assert len(s) == sum(range(5))
        assert len(s2) == sum(range(5))

    def testFoldValueOverflow(self):
        '''When passing a value larger than the defined bit-width can contain, a CreationError should be thrown.'''

        blob = self.Blob(2**8, 1, 1, 1)
        try_fold = lambda: fold(blob)
        self.assertRaises(CreationError, try_fold)

    def testFoldMissingAttribute(self):
        '''
        When an object to be folded is missing attributes named in
        it's class's fold_format string, an AttributeError is thrown.
        '''

        blob = self.Blob(0)
        try_fold = lambda: fold(blob)

        self.assertRaises(AttributeError, try_fold)
